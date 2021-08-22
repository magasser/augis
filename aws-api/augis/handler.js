/**
 * Authors: Manuel Gasser und Julian Haldimann
 * Created: 20.03.2021
 * Last Modified: 20.03.2021
 */

const awsSlsExpress = require('aws-serverless-express');
const app = require('./src/index');

const server = awsSlsExpress.createServer(app);

exports.handler = (event, context) => {
    return awsSlsExpress.proxy(server, event, context);
};