/**
 * Authors: Manuel Gasser, Julian Haldimann
 * Created: 20.03.2021
 * Last Modified: 01.05.2021
 */

const express = require('express');
const dotenv = require("dotenv");
const mysql = require('mysql');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');

const routes = express.Router({
    mergeParams: true
});

// get config vars
dotenv.config();

// Connection Data is outsourced in a config file
let db = mysql.createConnection({
    host: process.env.SQL_HOST,
    user: process.env.SQL_USER,
    password: process.env.SQL_PASSWORD,
    database: process.env.SQL_DATABASE,
});

/**
 * Create a connection a message on console
 */
db.connect((err) => {
    if (err) throw err;
});


routes.get('/', (req, res) => {
    res.status(200).json({test: 'It works like a charm!'});
});

/**
 * Generate a JWT with a username, token and an expireDate.
 *
 * @param username
 * @returns promise from jwt.sign
 */
let generateToken = (username) => {
    // 10800 means 3 Hours
    return jwt.sign({username: username}, process.env.TOKEN_SECRET, {expiresIn: 10800});
};

/**
 * Route to check if the token received from browser is a valid token.
 */
routes.post('/is-valid', ((req, res) => {
    checkToken(req.headers.authorization.replace('Bearer ', ''), res, (dec) => {
        res.status(200).send(dec);
    });
}));

/**
 * Route to get the mqtt credentials.
 * The JWT must be correct to get the credentials.
 */
routes.get('/mqtt-credentials', ((req, res) => {
    checkToken(req.headers.authorization.replace('Bearer ', ''), res, () => {
        res.status(200).send({
            domain: process.env.MQTT_DOMAIN,
            username: process.env.MQTT_USER,
            password: process.env.MQTT_PASSWORD
        });
    });
}));

/**
 * Check if the token is valid else send an error to the browser.
 *
 * @param token The received JWT
 * @param res The Response reference
 * @param f A function which will be executed if the token is valid
 */
let checkToken = (token, res, f) => {
    jwt.verify(token, process.env.TOKEN_SECRET, (err, decoded) => {
        if (err) return res.status(500).send({auth: false, message: 'Failed to authenticate token.'});

        f(decoded);
    });
}

/**
 * Compare the login credentials against the users in the database.
 */
routes.post('/login', (req, res) => {
    const data = JSON.parse(req.body.data);

    const name = data.username;

    let pw = data.password;

    // Get matching user from database
    db.query(`SELECT password, id
              FROM user
              WHERE username LIKE '${name}'`, (err, result) => {
        if (result.length !== 0) {
            // Compare received password to hash in database
            bcrypt.compare(pw, result[0].password, (err, r) => {
                if (r) {
                    let token = generateToken(name);
                    let json = `{ "status":"success", "userid": "${result[0].id}", "token": "${token}" }`;
                    res.write(json)
                    res.end()
                } else {
                    res.send(JSON.parse('{ "status":"failed"}'))
                }
            });
        } else {
            res.send(JSON.parse('{ "status":"failed"}'));
        }
    });
});

/**
 * Route to insert a new route entry into the database and add
 * the corresponding geojson file on the VM.
 */
routes.post('/save-route', function (req, res) {
    try {
        const data = JSON.parse(req.body.data);

        db.query(`SELECT id
                  FROM lakes
                  WHERE name LIKE '${data.lake}'`, (err, result) => {
            if (err) return res.status(500).send({auth: false, message: 'Failed to find lake.'});

            db.query(`INSERT INTO routes (name, json, date, description, lake)
                      VALUES ('${data.name}', '${JSON.stringify(data.json)}', NOW(), '${data.description}', ${result[0].id})`, (err, result) => {
                if (err) return res.status(500).send({auth: false, message: 'Failed to add route to database.'});

                res.send('success');
            });
        })
    } catch (ex) {
        console.error(ex);
        res.send('Could not parse JSON');
    }
});

/**
 * Route to insert a new route entry into the database and add
 * the corresponding geojson file on the VM.
 */
routes.post('/save-ride', function (req, res) {
    try {
        const data = JSON.parse(req.body.data);

        db.query(`SELECT id
                  FROM lakes
                  WHERE name LIKE '${data.lake}'`, (err, result) => {
            if (err) return res.status(500).send({auth: false, message: 'Failed to find lake.'});

            db.query(`INSERT INTO rides (name, json, date, description, lake)
                      VALUES ('${data.name}', '${JSON.stringify(data.json)}', NOW(), '${data.description}', ${result[0].id})`, (err, result) => {
                if (err) return res.status(500).send({auth: false, message: 'Failed to add route to database.'});

                res.send('success');
            });
        })
    } catch (ex) {
        console.error(ex);
        res.send('Could not parse JSON');
    }
});


/**
 * Get all the routes from the database.
 */
routes.get('/routes', function (req, res) {
    db.query('SELECT * FROM routes', (err, result) => {
        if (err) return res.status(500).send({auth: false, message: 'Failed to get routes.'});

        res.set('Content-Type', 'application/json');
        res.send(result);
    });
});

/**
 * Get all the routes from the database.
 */
routes.get('/rides', function (req, res) {
    db.query('SELECT * FROM rides', (err, result) => {
        if (err) return res.status(500).send({auth: false, message: 'Failed to get rides°°.'});

        res.set('Content-Type', 'application/json');
        res.send(result);
    });
});

/**
 * Get a specific route by its name.
 * :name means --> /routes/routename
 */
routes.get('/routes/:name', function (req, res) {
    db.query(`SELECT *
              FROM routes
              WHERE name LIKE '${req.params.name}'`, (err, result) => {
        if (err) return res.status(500).send({auth: false, message: 'Failed to get route.'});

        res.set('Content-Type', 'application/json');
        res.send(result[0]);
    });
});

/**
 * Get a specific route by its id.
 */
routes.get('/routes/id/:id', function (req, res) {
    db.query(`SELECT *
              FROM routes
              WHERE id = ${req.params.id}`, (err, result) => {
        if (err) return res.status(500).send({auth: false, message: 'Failed to get route.'});

        res.set('Content-Type', 'application/json');
        res.send(result[0]);
    });
});

/**
 * Get all lakes from the databsae.
 */
routes.get('/lakes', function (req, res) {
    db.query('SELECT * FROM lakes', (err, result) => {
        if (err) return res.status(500).send({auth: false, message: 'Failed to get lakes.'});

        res.set('Content-Type', 'application/json');
        res.send(result);
    });
});

/**
 * Get specific lake by its name.
 */
routes.get('/lakes/:name', function (req, res) {
    db.query(`SELECT *
              FROM lakes
              WHERE name LIKE '${req.params.name}'`, (err, result) => {
        if (err) return res.status(500).send({auth: false, message: 'Failed to get lake.'});

        res.set('Content-Type', 'application/json');
        res.send(result[0]);
    });
});

/**
 * Get specific lake by its id.
 */
routes.get('/lakes/id/:id', function (req, res) {
    db.query(`SELECT *
              FROM lakes
              WHERE id = ${req.params.id}`, (err, result) => {
        if (err) return res.status(500).send({auth: false, message: 'Failed to get lake.'});

        res.set('Content-Type', 'application/json');
        res.send(result[0]);
    });
});

module.exports = {
    routes,
};
