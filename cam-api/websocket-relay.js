// Use the websocket-relay to serve a raw MPEG-TS over WebSockets. You can use
// ffmpeg to feed the relay. ffmpeg -> websocket-relay -> browser
// Example:
// node websocket-relay yoursecret 8081 8082
// ffmpeg -i <some input> -f mpegts http://localhost:8081/yoursecret

// Script from: https://github.com/phoboslab/jsmpeg

var fs = require('fs'),
    http = require('http'),
    WebSocket = require('ws');

var https = require('https');

if (process.argv.length < 3) {
    console.log(
        'Usage: \n' +
        'node websocket-relay.js <secret> [<stream-port> <websocket-port>]'
    );
    process.exit();
}

var STREAM_SECRET = process.argv[2],
    STREAM_PORT = process.argv[3] || 8081,
    WEBSOCKET_PORT = process.argv[4] || 8082,
    RECORD_STREAM = false;


var options = {
    cert: fs.readFileSync('/etc/letsencrypt/live/augis.ti.bfh.ch/cert.pem'),
    key: fs.readFileSync('/etc/letsencrypt/live/augis.ti.bfh.ch/privkey.pem')
};

let camClients = {};
let cams = [];

var camServer = http.createServer(function (req, resp) {
    var params = req.url.substr(1).split('/');

    if (params[0] !== STREAM_SECRET) {
        console.log(
            'Failed Stream Connection: ' + req.socket.remoteAddress + ':' +
            req.socket.remotePort + ' - wrong secret.'
        );
        resp.end();
    }
    let id = params[1];
    if (!cams.includes(id)) {
        cams.push(id);
        camClients[id] = [];
    }
    resp.connection.setTimeout(0);

    console.log('New Camera ' + id);
    console.log(
        'Stream Connected: ' +
        req.socket.remoteAddress + ':' +
        req.socket.remotePort
    );

    req.on('data', function (data) {
        socketServer.broadcast(data, params[1]);
        if (req.socket.recording) {
            req.socket.recording.write(data);
        }
    });
    req.on('end', function () {
        console.log('close');
        if (req.socket.recording) {
            req.socket.recording.close();
        }
    });

    // Record the stream to a local file?
    if (RECORD_STREAM) {
        var path = 'recordings/' + Date.now() + '.ts';
        req.socket.recording = fs.createWriteStream(path);
    }
});

// HTTP Server to accept incomming MPEG-TS Stream from ffmpeg
var streamServer = https.createServer(options, function (req, resp) {
    var params = req.url.substr(1).split('/');

    if (params[0] !== STREAM_SECRET) {
        console.log(
            'Failed Stream Connection: ' + req.socket.remoteAddress + ':' +
            req.socket.remotePort + ' - wrong secret.'
        );
        resp.end();
    }

    resp.connection.setTimeout(0);
    console.log(
        'Stream Connected: ' +
        req.socket.remoteAddress + ':' +
        req.socket.remotePort
    );
    req.on('data', function (data) {
        socketServer.broadcast(data, params[1]);
        if (req.socket.recording) {
            req.socket.recording.write(data);
        }
    });
    req.on('end', function () {
        console.log('close');
        if (req.socket.recording) {
            req.socket.recording.close();
        }
    });

    // Record the stream to a local file?
    if (RECORD_STREAM) {
        var path = 'recordings/' + Date.now() + '.ts';
        req.socket.recording = fs.createWriteStream(path);
    }
})


// Websocket Server
var socketServer = new WebSocket.Server({server: streamServer, perMessageDeflate: false});
socketServer.connectionCount = 0;
socketServer.on('connection', function (socket, upgradeReq) {
    socketServer.connectionCount++;
    let params = upgradeReq.url.split('/');
    let id = params[2];
    if (!cams.includes(id)) {
        cams.push(id);
        camClients[id] = [];
    }

    camClients[id].push(socket);
    console.log('New Client for Camera ' + id);
    console.log(
        'New WebSocket Connection: ',
        (upgradeReq || socket.upgradeReq).socket.remoteAddress,
        (upgradeReq || socket.upgradeReq).headers['user-agent'],
        '(' + socketServer.connectionCount + ' total)'
    );
    socket.on('close', function (code, message) {
        socketServer.connectionCount--;
        console.log(
            'Disconnected WebSocket (' + socketServer.connectionCount + ' total)'
        );
    });
});
socketServer.broadcast = function (data, id) {
    camClients[id].forEach(function each(client) {
        if (client.readyState === WebSocket.OPEN) {
            client.send(data);
        }
    });
};

// Keep the socket open for streaming
streamServer.headersTimeout = 0;
streamServer.listen(WEBSOCKET_PORT);
camServer.headersTimeout = 0;
camServer.listen(STREAM_PORT);


console.log('Listening for incomming MPEG-TS Stream on http://127.0.0.1:' + STREAM_PORT + '/<secret>');
console.log('Awaiting WebSocket connections on wss://127.0.0.1:' + WEBSOCKET_PORT + '/');
