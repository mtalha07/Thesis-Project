// Initialize the map
var map = L.map('map').setView([31.5497, 74.3436], 13); // Lahore coordinates

// Add OpenStreetMap tiles to the map
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// Add an empty layer group for markers
var markersLayer = L.layerGroup().addTo(map);

// Add a click event listener to the map
map.on('click', function(e) {
    // Clear existing markers
    markersLayer.clearLayers();

    // Create a marker for the clicked location
    var clickedMarker = L.marker(e.latlng).addTo(markersLayer);

    // Get the coordinates of the clicked location
    var startLatLng = {
        lat: e.latlng.lat,
        lng: e.latlng.lng
    };

    var hospitalsDropdown = document.getElementById('hospitalsDropdown');
    var selectedHospitalId = hospitalsDropdown.value;

    if (!selectedHospitalId) {
        alert('Please select a hospital from the dropdown.');
        return;
    }

    var data = {
        marker: {
            lat: startLatLng.lat,
            lng: startLatLng.lng
        },
        hospital: selectedHospitalId
    };

    // Call the API to calculate the route
    fetch('/api/route', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to fetch route');
        }
        return response.json();
    })
    .then(data => {
        if (!data.path) {
            throw new Error('Invalid route data received');
        }

        // Create a marker for the hospital
        var hospitalMarker = L.marker([data.path[0][1], data.path[0][0]]).addTo(markersLayer);

        // Create a polyline for the route
        var pathCoordinates = data.path.map(coord => [coord[1], coord[0]]);
        var path = L.polyline(pathCoordinates, { color: 'blue' }).addTo(map);
        map.fitBounds(path.getBounds());
    })
    .catch(error => {
        console.error('Error fetching or drawing route:', error);
        // You can add additional error handling here, such as showing an alert to the user
    });
});
