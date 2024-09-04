from flask import Flask, render_template, request
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import sqlite3

app = Flask(__name__)

class RecommendationModel:
    def __init__(self, db_path):
        self.db_path = db_path
        self.data = None
        self.assets = None
        self.cv = CountVectorizer()
        self.cosine_sim_matrix = None
        self._prepare_data()

    def _prepare_data(self):
        conn = sqlite3.connect(self.db_path)
        self.data = pd.read_sql_query("SELECT * FROM locations", conn)
        self.assets = pd.read_sql_query("SELECT * FROM assetloc", conn)
        conn.close()

        # Gabungkan data locations dengan assets berdasarkan 'tempat'
        self.data = pd.merge(self.data, self.assets, on='tempat', how='left')
        self.data['features'] = self.data[['tempat', 'tema', 'tipe', 'alamat']].fillna('').astype(str).agg(' '.join, axis=1)
        count_matrix = self.cv.fit_transform(self.data['features'])
        self.cosine_sim_matrix = cosine_similarity(count_matrix, count_matrix)

    def get_recommendations(self, location_name, top_n=5, threshold=0):
        if location_name not in self.data['tempat'].values:
            return []
        indices = pd.Series(self.data.index, index=self.data['tempat']).drop_duplicates()
        idx = indices[location_name]
        sim_scores = list(enumerate(self.cosine_sim_matrix[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = [score for score in sim_scores if score[1] > threshold and score[0] != idx]
        sim_scores = sim_scores[:top_n]
        recommendations = []
        for i, score in sim_scores:
            rec = self.data.iloc[i].to_dict()
            rec['similarity'] = score  # Menambahkan cosine similarity ke dalam dictionary
            recommendations.append(rec)
        return recommendations


model = RecommendationModel(db_path='data/locations.db')

@app.route('/')
def index():
    sort_by_type = request.args.get('sortbytype', None)
    sort_by_tema = request.args.get('sortbytema', None)
    sort_by_harga = request.args.get('sortbyharga', None)
    
    filtered_df = model.data.copy()
    
    if sort_by_type:
        filtered_df = filtered_df[filtered_df['tipe'] == sort_by_type]
    
    if sort_by_tema:
        filtered_df = filtered_df[filtered_df['tema'] == sort_by_tema]
    
    if sort_by_harga:
        filtered_df = filtered_df.sort_values(by='harga', ascending=(sort_by_harga == 'asc'))
    
    locations = filtered_df.to_dict('records')
    unique_tipes = model.data['tipe'].unique()
    unique_temas = model.data['tema'].unique()
    
    return render_template('index.html', locations=locations, unique_tipes=unique_tipes, unique_temas=unique_temas)


@app.route('/detail/<location_name>')
def info(location_name):
    if location_name not in model.data['tempat'].values:
        return "Location not found", 404
    location = model.data[model.data['tempat'] == location_name].iloc[0].to_dict()
    recommendations = model.get_recommendations(location_name)
    return render_template('info.html', location=location, recommendations=recommendations)


if __name__ == '__main__':
    app.run(debug=True)
