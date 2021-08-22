/**
 * Authors: Manuel Gasser, Julian Haldimann
 * Created: 17.11.2020
 * Updated: 03.06.2021
 */

// Topics from MQTT
const Topics = {
    ITEM_ROUTE_ID: 'augis/item/route',
    ITEM_CURRENT_ROUTE: 'augis/item/current-route',
    SENSOR_GPS: 'augis/sensor/gps/phone',
    SENSOR_GPS_RTK: 'Rover/9C8BE24C22/event',
    SENSOR_HEADING: 'augis/sensor/heading',
    COMMAND_DRIVE: 'augis/command/drive',
    COMMAND_MODE: 'augis/command/mode',
    COMMAND_ENGINE: 'augis/command/engine',
    INFO_STATUS: 'augis/info/status',
    INFO_MODE: 'augis/info/mode',
    INFO_SPEED: 'augis/info/speed',
    INFO_CONN: 'augis/info/conn',
    ERROR_CONN: 'augis/error/conn',
    LWT: 'augis/lwt',
    HELLO_REQ: 'augis/hello/req',
    HELLO_RESP: 'augis/hello/resp',
    RECORD: 'augis/record'
};

// Variables for map
let map;
let routePointsAUGIS = [];
let routeJson;
let routeCreated;
let startPos;
let currentPos;
let routeSegments = [];
let oldLine;

// Mqtt client
let client;
let mode = 'radio-remote';

window.onload = () => {
    validateToken(loadPage);
};

/**
 * If the page is loaded load the map and the routes and connect to MQTT
 */
let loadPage = () => {

    loadMap();
    loadRoutes();

    fetch(`${host}/api/mqtt-credentials`, {
        method: 'GET',
        headers: {
            'Accept': '*/*',
            'Authorization': getCookie('token')
        }
    }).then((resp) => resp.json())
        .then(mqtt => {
            // Create a client instance
            client = new Paho.MQTT.Client(mqtt.domain, Number(443), "/ws", "client" + Math.floor(Math.random() * 100) + Date.now());

            // set callback handlers
            client.onConnectionLost = onConnectionLost;
            client.onMessageArrived = onMessageArrived;

            // last will of basestation
            let lwt = new Paho.MQTT.Message('base-station');
            lwt.destinationName = Topics.LWT;

            // connect the client
            client.connect({
                onSuccess: onConnect,
                userName: mqtt.username,
                password: mqtt.password,
                willMessage: lwt,
                useSSL: true,
            });
        });
    if (routePointsAUGIS.length === 0) {
        let saveButton = document.querySelector('.save-ride');
        saveButton.disabled = true;
    }

    loadLakes();

    updateValue('raspberry-conn', 'Establishing connection to Raspberry Pi...');
    updateValue('arduino-conn', 'Establishing connection to Arduino...');
    updateValue('rasp-ard-conn', 'Establishing Raspberry Pi to Arduino connection...');
    setSignal('raspberry-conn', 'yellow');
    setSignal('arduino-conn', 'yellow');
    setSignal('rasp-ard-conn', 'yellow');

    setTimeout(() => {
        if (getValue('raspberry-conn') === 'Establishing connection to Raspberry Pi...') {
            updateValue('raspberry-conn', 'Raspberry Pi not connected');
            setSignal('raspberry-conn', 'red');
        }
        if (getValue('arduino-conn') === 'Establishing connection to Arduino...') {
            updateValue('arduino-conn', 'Arduino not connected');
            setSignal('arduino-conn', 'red');
        }
        if (getValue('rasp-ard-conn') === 'Establishing Raspberry Pi to Arduino connection...') {
            updateValue('rasp-ard-conn', 'Raspberry Pi not connected to Arduino');
            setSignal('rasp-ard-conn', 'red')
        }
    }, 5000);

    setupStream();
};

/**
 * Function for stream setup from raspberry pi
 */
let setupStream = () => {
    let frontCanvas = document.getElementById('front-stream');
    let waterCanvas = document.getElementById('water-stream');
    let baseUrl = 'wss://augis.ti.bfh.ch:80/asdfghjkl/';
    let frontUrl = baseUrl + 'front';
    let waterUrl = baseUrl + 'water';
    let playerFront = new JSMpeg.Player(frontUrl, {canvas: frontCanvas});
    let playerWater = new JSMpeg.Player(waterUrl, {canvas: waterCanvas});
}

/**
 * Update line with route of AUGIS
 *
 * @return updated line
 */
let updateLine = () => {
    if (oldLine) {
        map.removeLayer(oldLine);
    }

    // Adjust color of line according to mode
    let color = mode === 'auto' ? 'green' : 'orange';

    oldLine = L.polyline(routePointsAUGIS, {color: color}).addTo(map);
    map.fitBounds(getBounds(routeSegments.concat([oldLine])), {padding: [100, 100]});

    return oldLine;
};

/**
 * Get bounds of multiple polylines.
 *
 * @param polylines to get the bounds from
 */
let getBounds = (polylines) => {
    let ne = [];
    let sw = [];
    // Set default minimum and maximum values to be overridden
    let maxLat = -90;
    let maxLng = -180;
    let minLat = 90;
    let minLng = 180;
    polylines.forEach(pl => {
        let bounds = pl.getBounds();
        ne.push(bounds._northEast);
        sw.push(bounds._southWest);
    });

    ne.forEach(p => {
        maxLat = p.lat > maxLat ? p.lat : maxLat;
        maxLng = p.lng > maxLng ? p.lng : maxLng;
    });
    sw.forEach(p => {
        minLat = p.lat < minLat ? p.lat : minLat;
        minLng = p.lng < minLng ? p.lng : minLng;
    });

    return [
        [maxLat, maxLng],
        [minLat, minLng]
    ];
};

/**
 * Adds marker to map at the given location and creates
 * popup with the given title which appears on hover.
 *
 * @param loc location to set the marker
 * @param title of the marker
 * @return created marker
 */
let addMarker = (loc, title) => {
    let marker = L.marker(loc, {title: title}).addTo(map);
    let popup = L.popup()
        .setLatLng(marker._latlng)
        .setContent(`<p>${title}</p>` +
            `<p>WGS 84: ${loc[0]}, ${loc[1]}</p>`);
    marker.on('mouseover', (e) => {
        marker.bindPopup(popup).openPopup();
    });
    marker.on('mouseout', (e) => {
        marker.closePopup();
    });

    return marker;
};

/**
 * Remove marker from map.
 *
 * @param marker to be removed
 */
let removeMarker = (marker) => {
    map.removeLayer(marker);
};

/**
 * Function to load the map to show current position of the AUGIS.
 */
let loadMap = () => {
    map = L.map('map', {
        // Coordinates from region Bern / Biel
        center: [47.10708, 7.21701],
        zoom: 10
    });

    // Use the openstreetmap layer
    L.tileLayer('https://{s}.tile.osm.org/{z}/{x}/{y}.png', {
        maxZoom: 20,
        maxNativeZoom: 18
    }).addTo(map);
};

/**
 * Callback function if connection to MQTT-Broker was successful.
 */
function onConnect() {
    let options = {
        qos: 1,
    }
    client.subscribe(Topics.SENSOR_GPS);
    client.subscribe(Topics.SENSOR_GPS_RTK);
    client.subscribe(Topics.SENSOR_HEADING);
    client.subscribe(Topics.INFO_MODE, options);
    client.subscribe(Topics.INFO_STATUS, options);
    client.subscribe(Topics.INFO_SPEED, options);
    client.subscribe(Topics.INFO_CONN, options);
    client.subscribe(Topics.ERROR_CONN, options);
    client.subscribe(Topics.ITEM_CURRENT_ROUTE, options);
    client.subscribe(Topics.LWT, options);
    client.subscribe(Topics.HELLO_REQ, options)
    client.subscribe(Topics.HELLO_RESP, options);

    // Get current route if AUGIS is already driving
    sendMessage(Topics.ITEM_CURRENT_ROUTE, 'get');
    sendMessage(Topics.HELLO_REQ, 'base-station');
}

/**
 * Callback function when connection to MQTT-Broker is lost.
 */
function onConnectionLost(responseObject) {
    if (responseObject.errorCode !== 0) {
        console.log("onConnectionLost:" + responseObject.errorMessage);
    }
}

/**
 * Callback function when message from subscribed topic is received.
 *
 * @param msg message from mqtt
 */
function onMessageArrived(msg) {
    let topic = msg.destinationName;
    let payload = msg.payloadString;

    switch (topic) {
        case Topics.ITEM_CURRENT_ROUTE:
            if (payload.toLowerCase() !== 'none' && payload.toLowerCase() !== 'get') {
                routePointsAUGIS = parseGeoJSON(JSON.parse(payload));
                updateLine();

                let rideSave = document.querySelector('.save-ride');
                rideSave.disabled = false;
            }
            break;
        case Topics.SENSOR_GPS_RTK:
            let data = payload.split(',');
            const lat_rtk = Number(data[0]);
            const lng_rtk = Number(data[1]);
            if (currentPos) {
                removeMarker(currentPos);
            } else {
                startPos = addMarker([lat_rtk, lng_rtk], 'AUGIS Start Position');
            }
            currentPos = addMarker([lat_rtk, lng_rtk], 'Current Position AUGIS');
            routePointsAUGIS.push([lat_rtk, lng_rtk]);
            if (routePointsAUGIS.length === 1) {
                let rideSave = document.querySelector('.save-ride');
                rideSave.disabled = false;
            }
            updateLine();
            updateValue('gps', `${lat_rtk}, ${lng_rtk}`);
            break;
        case Topics.SENSOR_GPS:
            let coords = payload.split(',');
            const lat = coords[0];
            const lng = coords[1];

            /*if (currentPos) {
                removeMarker(currentPos);
            } else {
                startPos = addMarker([lat, lng], 'AUGIS Start Position');
            }
            currentPos = addMarker([lat, lng], 'Current Position AUGIS');
            routePointsAUGIS.push([lat, lng]);
            if(routePointsAUGIS.length === 1) {
                let rideSave = document.querySelector('.save-ride');
                rideSave.disabled = false;
            }
            updateLine();
            updateValue('gps', `${lat}, ${lng}`);*/
            break;
        case Topics.SENSOR_HEADING:
            updateValue('heading', payload);
            changeDirectionOfArrow(payload);
            break;
        case Topics.INFO_MODE:
            if (oldLine) {
                routeSegments.push(updateLine());
                routePointsAUGIS = [];
                routePointsAUGIS.push(currentPos._latlng);
                oldLine = undefined;
            }
            mode = payload;
            updateValue('mode', mode);
            let radioAuto = document.querySelector('#radio-auto');
            let radioRemote = document.querySelector('#radio-remote');
            let radioEmergency = document.querySelector('#radio-emergency');

            radioAuto.checked = payload === 'auto';
            radioRemote.checked = payload === 'radio-remote';
            radioEmergency.checked = payload === 'emergency';
            break;
        case Topics.INFO_STATUS:
            updateValue('status', payload);
            break;
        case Topics.INFO_SPEED:
            updateValue('speed', payload);
            break;
        case Topics.INFO_CONN:
            if (payload === 'rasp-ard') {
                updateValue('rasp-ard-conn', 'Raspberry Pi connected to Arduino');
                setSignal('rasp-ard-conn', 'green');
            }
            break;
        case Topics.ERROR_CONN:
            if (payload === 'rasp-ard') {
                updateValue('rasp-ard-conn', 'Raspberry Pi not connected to Arduino');
                setSignal('rasp-ard-conn', 'red');
            }
            break;
        case Topics.LWT:
            if (payload === 'raspberry') {
                updateValue('raspberry-conn', 'Raspberry Pi not connected');
                setSignal('raspberry-conn', 'red');
                updateValue('rasp-ard-conn', 'Raspberry Pi not connected to Arduino');
                setSignal('rasp-ard-conn', 'red');
            } else if (payload === 'arduino') {
                // updateValue('error', 'Lost MQTT connection to arduino.');
                // setSignal('error', 'red');
                updateValue('arduino-conn', 'Arduino not connected');
                setSignal('arduino-conn', 'red');
            }
            break;
        case Topics.HELLO_REQ:
            sendMessage(Topics.HELLO_RESP, 'base-station');
            break;
        case Topics.HELLO_RESP:
            if (payload === 'raspberry') {
                updateValue('raspberry-conn', 'Raspberry Pi connected');
                setSignal('raspberry-conn', 'green');
            } else if (payload === 'arduino') {
                updateValue('arduino-conn', 'Arduino connected');
                setSignal('arduino-conn', 'green');
            }
            break;
        default:
            console.warn(`No Handler for topic: ${topic}`)
    }
}

/**
 * Function to publish a message to the MQTT-Broker.
 *
 * @param topic The destination of the message
 * @param msg The message to send
 */
let sendMessage = (topic, msg) => {
    let message = new Paho.MQTT.Message(msg);
    message.qos = 2;
    message.destinationName = topic;
    client.send(message);
};

/**
 * Function called when slider values of the virtual remote control change.
 */
let onEngineSliderChanged = (update = false) => {
    const engineLeftSlider = document.querySelector('#engine-left-slider');
    const engineRightSlider = document.querySelector('#engine-right-slider');
    if (Math.abs(engineLeftSlider.value) < 30) {
        engineLeftSlider.value = 0;
    }
    if (Math.abs(engineRightSlider.value) < 30) {
        engineRightSlider.value = 0;
    }
    if (update) {
        sendMessage(Topics.COMMAND_ENGINE, `${engineLeftSlider.value},${engineRightSlider.value}`);
    }
};

/**
 * Function called when the slider for both engines is changed.
 */
let onBothEngineSliderChanged = () => {
    const bothSlider = document.querySelector('#both-engines-slider');
    const engineLeftSlider = document.querySelector('#engine-left-slider');
    const engineRightSlider = document.querySelector('#engine-right-slider');

    if (Math.abs(bothSlider.value) < 30) {
        bothSlider.value = 0;
    }

    engineLeftSlider.value = bothSlider.value;
    engineRightSlider.value = bothSlider.value;

    sendMessage(Topics.COMMAND_ENGINE, `${engineLeftSlider.value},${engineRightSlider.value}`);
}

/**
 * Function called when radio button is clicked.
 *
 * @param val value of the radio button
 */
let onRadioClicked = (val) => {
    sendMessage(Topics.COMMAND_MODE, val);
};

/**
 * Update the value of an information field.
 *
 * @param field to be updated
 * @param val new value
 */
let updateValue = (field, val) => {
    let elem = document.querySelector(`#${field}`).querySelector('.value');

    elem.innerHTML = val;
};

/**
 * Get value of an information field.
 *
 * @param id of the field
 */
let getValue = (id) => {
    let field = document.getElementById(id).querySelector('.value');

    return field.innerHTML;
}

/**
 * Set color of waring signal.
 *
 * @param id of the signal
 * @param color of the warning signal
 */
let setSignal = (id, color) => {
    const light = document.getElementById(id);
    const signal = light.querySelector('.signal');
    const bg = signal.querySelector('.light-background');
    const text = light.querySelector('p');

    signal.className = `signal ${color}-light`;
    bg.className = `light-background ${color}-background`;
    text.className = `value ${color}`;
};

/**
 * Load the routes from the database.
 */
let loadRoutes = () => {
    const select = document.querySelector('#choose-route');
    fetch(`${host}/api/routes`, {
        method: 'GET',
        headers: {
            'Accept': '*/*'
        },
    })
        .then(resp => resp.json())
        .then(result => {
            let options = '<option value=""></option>';
            result.forEach((r) => {
                options += `<option value="${r.name}">${r.name}</option>`;
            });
            select.innerHTML = options;
        });
};

/**
 * Load route from database and show it on the map.
 *
 * @param route to be shown
 */
let showRoute = (route) => {
    if (route === '') {
        routeJson = undefined;
        return;
    }

    if (routeCreated) {
        map.removeLayer(routeCreated);
    }

    fetch(`${host}/api/routes/${route}`, {
        method: 'GET',
        headers: {
            'Accept': '*/*'
        },
    })
        .then(resp => resp.json())
        .then(json => {
            routeJson = json;
            const points = parseGeoJSON(JSON.parse(json.json).features[0].geometry.coordinates[0]);

            routeCreated = L.polyline(points, {color: 'red'}).addTo(map);
            map.fitBounds(routeCreated.getBounds(), {padding: [100, 100]});
        });
};

/**
 * Parse geojson to array of GPS points.
 *
 * @param gj geojson file to be parsed
 */
let parseGeoJSON = (gj) => {
    let points = [];

    gj.forEach(f => {
        const lat = f[1];
        const lng = f[0];

        points.push([lat, lng]);
    });

    return points
}

/**
 * Start the selected route.
 */
let startRoute = () => {
    sendMessage(Topics.ITEM_ROUTE_ID, routeJson.id.toString());
    setTimeout(() => {
        sendMessage(Topics.COMMAND_DRIVE, 'start');
    }, 3000);
};

/**
 * Stop the route.
 */
let stopRoute = () => {
    sendMessage(Topics.COMMAND_DRIVE, 'stop');
}

/**
 * Return home to start point.
 */
let returnHome = () => {
    sendMessage(Topics.COMMAND_DRIVE, 'return')
}

/**
 * Upload route from local files.
 *
 * @param e event from file selection
 */
let uploadRoute = (e) => {
    const file = e.target.files[0];

    const reader = new FileReader();

    reader.onload = () => {
        const gj = reader.result;

        const points = parseGeoJSON(JSON.parse(gj).features[0].geometry.coordinates[0]);

        routeCreated = L.polyline(points, {color: 'red'}).addTo(map);
        map.fitBounds(routeCreated.getBounds(), {padding: [100, 100]});
    }

    reader.readAsBinaryString(file);
}

let saveRide = () => {
    const name = document.querySelector('#name').value;
    const lake = document.querySelector('#select-lake').value;
    const description = document.querySelector('#description').value;
    if (name === '' || lake === '') {
        console.error("Name or lake not selected");
        return;
    }
    let collection = createGeoJson(routePointsAUGIS, name);

    const data = {
        name: name,
        json: collection,
        description: description,
        lake: lake
    };

    fetch(`${host}/api/save-ride`, {
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
        collection.features[0]['geometry'].coordinates[0].push([e[1], e[0]]);
    });

    return collection;
};

/**
 * Change Direction Arrow in html
 * @param angle Direction as float
 */
let changeDirectionOfArrow = (angle) => {
    let img = document.querySelector(".direction-arrow");
    img.setAttribute("style", "transform: rotate(" + angle + "deg)");
}

let record = (value) => {
    sendMessage(Topics.RECORD, value);
}
