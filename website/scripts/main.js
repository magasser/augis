/**
 * Authors: Manuel Gasser, Julian Haldimann
 * Created: 03.11.2020
 * Last Modified: 01.06.2021
 */

let map;

let routeSpacing = 10;

let lineMarkers = [];
let routeMarkers = [];
let latlong = [];
let selectedMarker;
let geojson;
let routeCreateActive = false;
let routeCreateButton;
let rect;
let type = '';
let rectArea = [[0, 0], [0, 0], [0, 0], [0, 0]];

let rectFlags = {
    rectEditMode: false,
    rectCreateMode: false,
    rectSelected: false,
    rectDrawing: false
};

let oldMousePos = {
    lat: 0,
    lng: 0
};

window.onload = () => {
    validateToken(loadPage);
};

/**
 * Function to load the page after the login
 */
let loadPage = () => {
    routeCreateButton = document.getElementById('route-create');
    const routeSpacingInput = document.getElementById('route-spacing');
    routeSpacingInput.value = routeSpacing;
    routeCreateButton.disabled = !routeCreateActive;
    map = L.map('map',
        {
            // Coordinates from region Bern / Biel
            center: [47.10708, 7.21701],
            zoom: 10
        });
    // Use the openstreetmap layer
    L.tileLayer('https://{s}.tile.osm.org/{z}/{x}/{y}.png', {
        maxZoom: 20,
        maxNativeZoom: 18
    }).addTo(map);

    // If the map get clicked a marker will be placed
    map.on('click', (e) => {
        if (rectFlags.rectCreateMode) return;

        let marker = L.marker(e.latlng).addTo(map);
        marker.on('click', (e) => {
            let lat = document.getElementById('lat');
            let lng = document.getElementById('lng');
            lat.value = marker._latlng.lat;
            lng.value = marker._latlng.lng;
            selectedMarker = marker;
        });
        lineMarkers.push(marker);
    });

    map.on('mousemove', (e) => {
        if (rectFlags.rectCreateMode && rectFlags.rectDrawing) {
            rectArea[1] = [rectArea[1][0], e.latlng.lng];
            rectArea[2] = [e.latlng.lat, e.latlng.lng];
            rectArea[3] = [e.latlng.lat, rectArea[3][1]];
            if (rect) {
                rect.removeFrom(map);
            }
            rect = createRect(rectArea);

            rectRotCenter = [rectArea[2][0] + (rectArea[0][0] - rectArea[2][0]) / 2,
                rectArea[2][1] + (rectArea[3][1] - rectArea[2][1]) / 2];

            oldMousePos.lat = e.latlng.lat;
            oldMousePos.lng = e.latlng.lng;
        }
    });

    map.on('mousedown', (e) => {
        if (rectFlags.rectCreateMode) {
            rectArea[0] = [e.latlng.lat, e.latlng.lng];
            rectArea[1] = [e.latlng.lat, e.latlng.lng];
            rectArea[2] = [e.latlng.lat, e.latlng.lng];
            rectArea[3] = [e.latlng.lat, e.latlng.lng];

            rect = createRect(rectArea);

            oldMousePos.lat = e.latlng.lat;
            oldMousePos.lng = e.latlng.lng;
            routeCreateActive = true;
            routeCreateButton.disabled = !routeCreateActive;
            rectFlags.rectDrawing = true;
        }
    });

    map.on('mouseup', (e) => {
        if (rectFlags.rectCreateMode) {
            rect.removeFrom(map);
            rect = createRectTransform(rectArea);
            // Timeout to stop click event from setting a marker when exiting rect create mode
            setTimeout(() => {
                rectFlags.rectCreateMode = false;
            }, 10);
            rectFlags.rectDrawing = false;
            map.dragging.enable();
        }
    });

    loadLakes();
}

/**
 * Creates a new Polygon from coordinates.
 *
 */
let createPolygon = () => {
    // Define JSON Header
    let collection = {
        "type": "FeatureCollection",
        "features": []
    };

    // Add the lineMarkers to the JSON File
    map.eachLayer(function (layer) {
        if (layer instanceof L.Marker) {
            collection.features.push(layer.toGeoJSON());
        }
    });

    let lats = [];
    let lngs = [];

    for (let i = 0; i < collection.features.length; i++) {
        lats.push(collection.features[i].geometry.coordinates[1]);
        lngs.push(collection.features[i].geometry.coordinates[0]);
    }

    // Calculate the max and min point to get the box
    let minlat = Math.min.apply(null, lats);
    let maxlat = Math.max.apply(null, lats);
    let minlng = Math.min.apply(null, lngs);
    let maxlng = Math.max.apply(null, lngs);

    rectArea = [[maxlat, minlng], [maxlat, maxlng], [minlat, maxlng], [minlat, minlng]];

    rect = createRectTransform(rectArea);
    routeCreateActive = true;
    routeCreateButton.disabled = !routeCreateActive;
};

/**
 * Creates a new Rectangle which can be transformed.
 *
 * @param area The area from which the rectangle is created
 */
let createRectTransform = (area) => {
    let r = L.rectangle(L.latLngBounds([
        area
    ]), {
        weight: 2,
        draggable: true,
        transform: true,
        interactive: true,
    }).addTo(map);
    r.transform.enable();

    return r
};

/**
 * Creates a new Rectangle
 *
 * @param area The area from which the rectangle is created
 */
let createRect = (area) => {
    return L.rectangle(area).addTo(map);
};

/**
 * Enable to create a rectangle.
 *
 */
let enableRectCreateMode = () => {
    rectFlags.rectCreateMode = true;
    map.dragging.disable();
    rectArea = [[0, 0], [0, 0], [0, 0], [0, 0]];
    if (rect) {
        rect.removeFrom(map);
    }
    rect = undefined;
    routeCreateActive = false;
    routeCreateButton.disabled = !routeCreateActive;
    removeLines();
};

/**
 * Creates a route from a rotated rectangle.
 *
 */
let createRotatedRouteInArea = () => {
    const area = rect.getLatLngs()[0];
    let tl = [area[1].lat, area[1].lng];
    let tr = [area[2].lat, area[2].lng];
    let bl = [area[0].lat, area[0].lng];
    let br = [area[3].lat, area[3].lng];

    const rotV = getAngle([bl, tl]);
    let rotH = getAngle([tl, tr]);
    const height = getLength([bl, tl]);
    const checkHeight = addMetersToCoordinate(routeSpacing, height);
    const width = getLength([tl, tr]);

    let pos = tl;

    routeMarkers.push(L.marker(pos));

    let orientation = 'horizontal_right';
    let line = [[0, 0], [0, 0]];
    let prevState = orientation;
    do {
        switch (orientation) {
            case 'horizontal_right':
                line = [[pos[0], pos[1]], [pos[0] + width, pos[1]]];
                line = rotateLine(line, rotH);
                pos = line[1];

                routeMarkers.push(L.marker(pos));

                prevState = orientation;
                orientation = 'vertical';
                break;
            case 'horizontal_left':
                line = [[pos[0], pos[1]], [pos[0] + width, pos[1]]];
                line = rotateLine(line, rotH + d2r(180));
                pos = line[1];

                routeMarkers.push(L.marker(pos));

                prevState = orientation;
                orientation = 'vertical';
                break;
            case 'vertical':
                line = [[pos[0], pos[1]], [addMetersToCoordinate(-routeSpacing, pos[0]), pos[1]]];
                line = rotateLine(line, rotV);
                pos = line[1];

                if (checkIsInRect([tl, tr], pos, checkHeight)) {
                    routeMarkers.push(L.marker(pos));
                }

                orientation = prevState === 'horizontal_left' ? 'horizontal_right' : 'horizontal_left';
                break;
        }
    } while (checkIsInRect([tl, tr], pos, checkHeight));

    createLine('area')
};

/**
 * Check if the actual position is in the area
 *
 */
let checkIsInRect = (points, pos, height) => {
    return getLength([points[0], pos]) <= height || getLength([points[1], pos]) <= height;
};

/**
 * Rotate a line by an angle
 * @param line The line to rotate
 * @param angle The angle for the line
 * @returns {*} Return the rotated line
 */
let rotateLine = (line, angle) => {
    let tmp = line;

    let x1 = tmp[1][0] - tmp[0][0];
    let y1 = tmp[1][1] - tmp[0][1];
    tmp[1][0] = Math.cos(angle) * x1 - Math.sin(angle) * y1;
    tmp[1][1] = Math.sin(angle) * x1 + Math.cos(angle) * y1;

    line[1][0] = tmp[1][0] + tmp[0][0];
    line[1][1] = tmp[1][1] + tmp[0][1];

    return line;
};

/**
 * Calculate the length
 * @param line Pass a line
 * @returns {number} Return the calculated
 */
let getLength = (line) => {
    let x = line[1][0] - line[0][0];
    let y = line[1][1] - line[0][1];

    return Math.sqrt(Math.pow(x, 2) + Math.pow(y, 2));
};

/**
 * Calculate the new direction to move
 * @param line Pass a line
 * @returns {number} Return the new Angle
 */
let getAngle = (line) => {
    let pos = {
        lat: line[0][0],
        lng: line[0][1]
    };
    let dest = {
        lat: line[1][0],
        lng: line[1][1]
    };

    const slope = (dest.lng - pos.lng) / (dest.lat - pos.lat);
    return Math.atan(slope);
};

/**
 * Converts Degrees into Radians.
 *
 */
let d2r = (degrees) => {
    return degrees * Math.PI / 180;
};

/**
 * Converts Radians into Degrees
 *
 * @param rad The angle to convert in radians
 */
let r2d = (rad) => {
    return rad * 180 / Math.PI;
};

/**
 * Creates a new Polygon from coordinates.
 *
 * @param distance The distance to add to the marker
 * @param pos The actual position of the marker
 * @return Returns the new position of the marker
 */
let addMetersToCoordinate = (distance, pos) => {
    let m = (1 / ((2 * Math.PI / 360) * 6378.137)) / 1000;
    return pos + (distance * m);
};

/**
 * Creates a new Line between two coordinates.
 *
 * @param type Give the type of the ....
 */
let createLine = (type) => {
    if (type === "area") {
        routeMarkers.forEach(e => {
            latlong.push(e._latlng)
        })
    } else {
        lineMarkers.forEach(e => {
            latlong.push(e._latlng)
        })
    }
    let polyline = L.polyline(latlong, {color: 'red'}).addTo(map);
    map.fitBounds(polyline.getBounds());
};

/**
 * Update existing marker with values from input fields
 *
 * @return selectedMarker The changed marker
 */
let updateMarker = () => {
    // Get the data from the input
    let lat = document.getElementById('lat');
    let lng = document.getElementById('lng');
    let pos = lineMarkers.indexOf(selectedMarker);
    selectedMarker.setLatLng([lat.value, lng.value]);
    lineMarkers[pos] = selectedMarker;
    return selectedMarker;
};

/**
 * Update spacing between routes with value in input field.
 */
let updateRouteSpacing = () => {
    const inputField = document.getElementById('route-spacing');
    routeSpacing = inputField.value;
}

/**
 * Show or hide the Save window
 * @param t Type of the file to save
 */
let toggleSavePopup = (t) => {
    let popup = document.getElementById('popup-wrapper');
    type = t;
    popup.classList.toggle("show");
};

/**
 * Creates a json file and auto download it
 *
 */
let saveRoute = () => {
    const name = document.querySelector('#name').value;
    const lake = document.querySelector('#select-lake').value;
    const description = document.querySelector('#description').value;
    if (name === '' || lake === '') {
        return;
    }
    let collection;

    switch (type) {
        case 'line':
            collection = createGeoJson(lineMarkers, name);
            break;
        case 'route':
            collection = createGeoJson(routeMarkers, name);
    }

    const data = {
        name: name,
        json: collection,
        description: description,
        lake: lake
    };

    fetch(`${host}/api/save-route`, {
        method: 'POST',
        headers: {
            'Accept': '*/*',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `data=${JSON.stringify(data)}`,
    })
        .then(response => response.text())
        .then(data => {
            console.log('Success:', data);
        })
        .catch((error) => {
            console.error('Error:', error);
        });

    toggleSavePopup(type);
};

/**
 * Generate a new Geojson file
 *
 * @param arr Data Array with all the coordinates inside
 * @param name Of the geojson to create
 * @return The generated
 */
let createGeoJson = (arr, name) => {
    // Create header for the geojson file
    let collection = {
        'type': 'FeatureCollection',
        'name': name,
        'crs': {
            type: 'name',
            properties: {
                "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
            }
        },
        'features': [
            {
                type: 'Feature',
                properties: {
                    id: 1,
                },
                geometry: {
                    type: "MultiLineString",
                    coordinates: [
                        []
                    ]
                }
            }
        ]
    };

    arr.forEach(e => {
        collection.features[0]['geometry'].coordinates[0].push([e._latlng['lng'], e._latlng['lat']]);
    });

    return collection;
};


/**
 * Removes an existing marker from the map
 *
 */
let removeMarker = () => {
    if (selectedMarker !== undefined) {
        map.removeLayer(selectedMarker);
        let pos = lineMarkers.indexOf(selectedMarker);
        lineMarkers.splice(pos, 1)
    }
};

/**
 * Removes every element (Marker, Lines, Polygons) from map
 *
 */
let clearMap = () => {
    // Remove every marker from the map
    lineMarkers.forEach(e => {
        map.removeLayer(e);
    });

    // Remove every line from the map
    removeLines();

    // Clear every array content
    lineMarkers = [];
    selectedMarker = [];
    latlong = [];
    routeMarkers = []
    routeCreateActive = false;
    routeCreateButton.disabled = !routeCreateActive;
};


/**
 * Remove all the lines from the map
 */
let removeLines = () => {
    for (i in map._layers) {
        if (map._layers[i]._path != undefined) {
            try {
                map.removeLayer(map._layers[i]);
            } catch (e) {
                console.error(`Problem with ${e} ${map._layers[i]}`);
            }
        }
    }
    routeMarkers = [];
    latlong = [];
};

/**
 * Toggle the dropdown window
 */
function toggleDropdown() {
    document.getElementById("myDropdown").classList.toggle("show-dropdown");
}

// Close the dropdown menu if the user clicks outside of it
window.onclick = function (event) {
    if (!event.target.matches('.dropbtn')) {
        var dropdowns = document.getElementsByClassName("dropdown-content");
        var i;
        for (i = 0; i < dropdowns.length; i++) {
            var openDropdown = dropdowns[i];
            if (openDropdown.classList.contains('show')) {
                openDropdown.classList.remove('show');
            }
        }
    }
};

/**
 * Get all lakes from database and add them to lake select options in save popup.
 */
let loadLakes = () => {
    const select = document.querySelector('#select-lake');
    fetch(`${host}/api/lakes`, {
        method: 'GET',
        headers: {
            'Accept': '*/*'
        },
    })
        .then(resp => resp.json())
        .then(result => {
            let options = '<option value=""></option>';
            result.forEach((r) => {
                let temp = r.name.charAt(0).toUpperCase() + r.name.slice(1)
                options += `<option value="${r.name}">${temp}</option>`;
            });
            select.innerHTML = options;
        });
}
