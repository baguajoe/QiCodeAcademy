process.env.NODE_ENV = process.env.NODE_ENV || "production";
const { merge } = require("webpack-merge");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const CssMinimizerPlugin = require("css-minimizer-webpack-plugin");
const common = require("./webpack.common.js");

module.exports = merge(common, {
  mode: "production",
  devtool: false,
  output: {
    filename: "js/[name].[contenthash:8].js",
    chunkFilename: "js/[name].[contenthash:8].chunk.js",
    clean: true,
  },
  module: {
    rules: [{ test: /\.css$/i, use: [MiniCssExtractPlugin.loader, "css-loader"] }],
  },
  plugins: [new MiniCssExtractPlugin({ filename: "css/[name].[contenthash:8].css" })],
  optimization: { minimizer: ["...", new CssMinimizerPlugin()] },
});
