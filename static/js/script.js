document.addEventListener('DOMContentLoaded', function() {
    var location = [{{ location['Latitude'] }}, {{ location['Longitude'] }}];
    var map = L.map('map').setView(location, 15);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    L.marker(location).addTo(map)
        .bindPopup('<b>{{ location["Tempat"] }}</b><br>{{ location["Alamat"] }}')
        .openPopup();
});

function changeMainImage(src) {
    document.getElementById('main-image').src = src;
}

