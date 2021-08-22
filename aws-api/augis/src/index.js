/**
 * Authors: Manuel Gasser, Julian Haldimann
 * Created: 20.03.2021
 * Last Modified: 20.03.2021
 */

const express = require('express');
const cors = require('cors');

const {
    routes: apiRoutes,
} = require('./api/routes');

const app = express();

app.use(express.json());
app.use(express.urlencoded());
app.use(cors({
    origin: '*',
    methods: 'OPTIONS, GET, POST',
    optionsSuccessStatus: 200
}));

app.use('/api', apiRoutes);

module.exports = app;
