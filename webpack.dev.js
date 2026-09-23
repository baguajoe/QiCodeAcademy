process.env.NODE_ENV = process.env.NODE_ENV || "development";
const { merge } = require("webpack-merge");
const common = require("./webpack.common.js");

const API = `http://127.0.0.1:${process.env.FLASK_PORT || 3001}`;

module.exports = merge(common, {
  mode: "development",
  devtool: "eval-cheap-module-source-map", // cheap source maps keep memory low
  output: { filename: "[name].js", chunkFilename: "[name].chunk.js" },
  module: {
    rules: [{ test: /\.css$/i, use: ["style-loader", "css-loader"] }],
  },
  cache: { type: "filesystem" },
  watchOptions: { ignored: /node_modules|dist_manual|\.venv|instance|uploads/ },
  devServer: {
    port: Number(process.env.WEBPACK_PORT || 3000),
    host: "0.0.0.0",
    allowedHosts: "all", // Codespaces forwarded URLs
    historyApiFallback: true,
    hot: true,
    compress: true,
    client: { overlay: { warnings: false, errors: true }, webSocketURL: "auto://0.0.0.0:0/ws" },
    // Also write to dist_manual so Flask on :3001 serves the latest build too.
    devMiddleware: { writeToDisk: true },
    static: false,
    proxy: [
      {
        context: ["/api", "/uploads", "/flask-admin", "/sitemap.xml", "/robots.txt"],
        target: API,
        changeOrigin: false,
      },
    ],
  },
});
