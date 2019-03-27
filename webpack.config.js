'use strict';

const webpack = require('webpack');
const path = require('path');

const ExtractTextWebpackPlugin = require('extract-text-webpack-plugin');
const OptimizeCssAssetsPlugin = require('optimize-css-assets-webpack-plugin');
const BundleTracker = require("webpack-bundle-tracker");

const prod = process.env.NODE_ENV === 'production';

let config = {
    context: path.resolve(__dirname, 'static'),
    mode: prod ? 'production' : 'development',
    entry: {
        'ehl-oenology-quizz': './js/index.js'
    },
    output: {
        path: path.resolve(__dirname, './static/compiled'),
        filename: '[name]-[hash].min.js',
        publicPath: '/static/compiled/'
    },
    resolve: {
        unsafeCache: !prod
    },
    module: {
        rules: [
            {
                test: /\.js$/,
                exclude: /node_modules/,
                loader: 'babel-loader'
            },
            {
                test: /\.scss$/,
                use: ExtractTextWebpackPlugin.extract({
                    fallback: 'style-loader',
                    use: [
                        {
                            loader: 'css-loader',
                            options: { sourceMap: !prod }
                        },
                        {
                            loader: 'sass-loader',
                            options: { sourceMap: !prod }
                        },
                        'postcss-loader'
                    ],
                })
            },
            {
                test: /\.(eot|svg|ttf|woff|woff2)$/,
                loader: 'file-loader?name=/fonts/[name].[ext]'
            },
            {
                test: /\.(png|jpe?g|gif)$/,
                loader: 'file-loader?name=/images/[name].[ext]'
            }
        ]
    },
    plugins: [
        new ExtractTextWebpackPlugin('[name]-[hash].min.css'),
        new webpack.LoaderOptionsPlugin({
            debug: !prod
        }),
        new BundleTracker({
            filename: './webpack-stats.json'
        })
    ],
    optimization: {
        splitChunks: {
            cacheGroups: {
                commons: {
                    test: /[\\/]node_modules[\\/]/,
                    name: 'vendor',
                    filename: '[name]-[hash].min.js',
                    chunks: 'all',
                }
            }
        },
        minimize: prod
    },
    devServer: {
        contentBase: path.resolve(__dirname, './web'),
        headers: {
            'Access-Control-Allow-Origin': '*'
        },
        historyApiFallback: true,
        inline: true,
        open: false,
        hot: true
    },
    devtool: prod ? undefined : 'eval-source-map'
};

if (prod)
{
    config.plugins.push(new OptimizeCssAssetsPlugin({
        cssProcessor: require('cssnano'),
        cssProcessorOptions: { discardComments: { removeAll: true } },
        canPrint: true
    }));
}

module.exports = config;
