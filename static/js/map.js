
const extent = [12659124.284612102, 2529362.467801116, 12751317.197575515, 2579348.791374634];

const view = new ol.View({
    center: [12705251.369968547, 2554325.000713136],
    zoom: 11.31937932503744,
    extent: extent,
});

const map = new ol.Map({
    layers: [
        new ol.layer.Tile({
        source: new ol.source.OSM(),
        }),
    ],
    target: 'map',
    view: view,
});

// Ensure the map is rendered before fitting the extent
map.once('postrender', function() {
    view.fit(extent);
});

document.onmousemove = function(e) {
    var x = e.pageX;
    var y = e.pageY;
    var coords = ol.proj.transform(map.getCoordinateFromPixel([x, y]), 'EPSG:3857', 'EPSG:4326');
    document.getElementById('position-pointer').innerHTML = 'Longitude: ' + coords[0] + ' Latitude: ' + coords[1];
    document.getElementById('position-zoom').innerHTML = 'Zoom: ' + view.getZoom();
}

document.onmousedown = function(e) {
    var x = e.pageX;
    var y = e.pageY;
    var coords = ol.proj.transform(map.getCoordinateFromPixel([x, y]), 'EPSG:3857', 'EPSG:4326');
    var text = coords[0] + ',' + coords[1];
    navigator.clipboard.writeText(text).then(function() {
        console.log('Async: Copying to clipboard was successful!');
    }, function(err) {
        console.error('Async: Could not copy text: ', err);
    });
}

function loadPinpointData(data) {
    data = JSON.parse(data);
    // add pinpoint data to map, data contains:
    // - name
    // - latitude (lat)
    // - longitude (long)
    // - description
    // only use lat and long for the pinpoint
    var features = [];
    for (var i = 0; i < data.length; i++) {
        var feature = new ol.Feature({
            geometry: new ol.geom.Point(ol.proj.fromLonLat([data[i].long, data[i].lat])),
            name: data[i].name,
            description: data[i].description,
            id: data[i]._id, // Add the ID to the feature
        });
        features.push(feature);
    }

    var vectorSource = new ol.source.Vector({
        features: features,
    });

    var iconStyle = new ol.style.Style({
        image: new ol.style.Icon({
            anchor: [0.5, 1],
            src: 'static/images/pinpoint.png',
            scale: 0.03,
        }),
    });

    var vectorLayer = new ol.layer.Vector({
        source: vectorSource,
        style: iconStyle,
    });

    map.addLayer(vectorLayer);

    // Create a div element for displaying the pinpoint name
    var pinpointDiv = document.getElementById('pinpoint-overlay');
    pinpointDiv.style.opacity = '0'; // Hide the div initially

    // Add event listener for pointer move
    map.on('pointermove', function (evt) {
        // Change cursor style on hover
        var hit = map.hasFeatureAtPixel(evt.pixel);
        map.getTargetElement().style.cursor = hit ? 'pointer' : '';

        // Check if a feature is found at the pointer position
        var featureFound = false;
        map.forEachFeatureAtPixel(evt.pixel, function (feature) {
            var name = feature.get('name');
            var description = feature.get('description');
            var pixel = evt.pixel;

            // Update the content and position of the div
            pinpointDiv.innerHTML = '';

            // Create title
            var title = document.createElement('h3');
            title.classList.add('pinpoint-title');
            title.innerHTML = name;
            pinpointDiv.appendChild(title);

            // Create description
            var desc = document.createElement('p');
            desc.classList.add('pinpoint-description');
            desc.innerHTML = description;
            pinpointDiv.appendChild(desc);

            // Check if the feature is within the threshold distance
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(function (position) {
                    var userCoords = [position.coords.longitude, position.coords.latitude];
                    console.log(userCoords)
                    var threshold = 100; // Distance threshold in meters

                    var featureCoords = feature.getGeometry().getCoordinates();
                    var distance = ol.sphere.getDistance(
                        ol.proj.toLonLat(featureCoords),
                        userCoords
                    );
                    if (distance < threshold) {
                        // Create checkpoint paragraph
                        var checkpoint = document.createElement('p');
                        checkpoint.classList.add('pinpoint-checkpoint');
                        checkpoint.innerHTML = 'Claim Checkpoint!';
                        pinpointDiv.appendChild(checkpoint);
                    }
                });
            }

            pinpointDiv.style.left = (pixel[0] + 10) + 'px'; // Offset by 10px to the right
            pinpointDiv.style.top = (pixel[1] + 10) + 'px'; // Offset by 10px down
            pinpointDiv.style.opacity = '1'; // Show the div
            featureFound = true;
        });

        if (!featureFound) {
            pinpointDiv.style.opacity = '0'; // Hide the div if no feature is found
        }
    });

    // Add event listener for click
    map.on('click', function (evt) {
        map.forEachFeatureAtPixel(evt.pixel, function (feature) {
            var id = feature.get('id');
            if (id) {
                window.location.href = '/pinpoint/' + id; // Navigate to the URL with the pinpoint ID
            }
        });
    });

    // Display user's location on the map
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function (position) {
            var userCoords = [position.coords.longitude, position.coords.latitude];
            console.log(userCoords)
            var userFeature = new ol.Feature({
                geometry: new ol.geom.Point(ol.proj.fromLonLat(userCoords)),
                name: 'Your Location',
                description: 'Your Location',
            });

            var userIconStyle = new ol.style.Style({
                image: new ol.style.Icon({
                    anchor: [0.5, 1],
                    src: 'static/images/user_location.png', // Replace with the path to your user location icon
                    scale: 0.05, // Adjust the scale as needed
                }),
            });

            userFeature.setStyle(userIconStyle);

            var userVectorSource = new ol.source.Vector({
                features: [userFeature],
            });

            var userVectorLayer = new ol.layer.Vector({
                source: userVectorSource,
            });

            map.addLayer(userVectorLayer);

            // Check distance to landmarks and change color if close
            var threshold = 100; // Distance threshold in meters
            features.forEach(function (feature) {
                var featureCoords = feature.getGeometry().getCoordinates();
                var distance = ol.sphere.getDistance(
                    ol.proj.toLonLat(featureCoords),
                    userCoords
                );
                if (distance < threshold) {
                    feature.setStyle(new ol.style.Style({
                        image: new ol.style.Icon({
                            anchor: [0.5, 1],
                            src: 'static/images/pinpoint.png', // Replace with the path to your green pinpoint icon
                            scale: 0.04,
                        }),
                    }));
                }
            });
        });
    } else {
        console.error('Geolocation is not supported by this browser.');
    }
}

function centerLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function (position) {
            var userCoords = [position.coords.longitude, position.coords.latitude];
            map.getView().setCenter(ol.proj.fromLonLat(userCoords));
            map.getView().setZoom(17); // Adjust the zoom level as needed
        });
    } else {
        console.error('Geolocation is not supported by this browser.');
    }
}