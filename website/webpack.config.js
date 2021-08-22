/**
 * Authors: Manuel Gasser, Julian Haldimann
 * Created: 08.12.2020
 * Last Modified: 19.03.2021
 */

const ExtractTextPlugin = require('extract-text-webpack-plugin');

module.exports = {
    entry: {
        'styles': [
            './styles/dropdown.scss',
            './styles/login.scss',
            './styles/main.scss',
            './styles/routes.scss',
            './styles/styles.scss',
            './styles/drive.scss',
            './styles/about.scss',
        ],
    },
    module: {
        rules: [
            {
                test: /\.scss$/,
                use: ExtractTextPlugin.extract({
                    fallback: 'style-loader',
                    use: ['css-loader', 'sass-loader']
                })
            }
        ]
    },
    plugins: [
        new ExtractTextPlugin('[name].css')
    ],
    stats: {
        warnings: false,
        version: true,
        chunks: false,
        children: false,
        env: true,
        timings: true,
    }
};
