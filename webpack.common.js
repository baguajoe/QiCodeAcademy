const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const CopyPlugin = require("copy-webpack-plugin");

const OUT = path.resolve(__dirname, "dist_manual");

module.exports = {
  entry: { app: "./src/front/js/index.js" },
  output: {
    path: OUT,
    publicPath: "/",
  },
  resolve: { extensions: [".js", ".jsx"] },
  module: {
    rules: [
      {
        test: /\.jsx?$/,
        exclude: /node_modules/,
        use: { loader: "babel-loader", options: { cacheDirectory: true } },
      },
      {
        // Site photos dropped into src/front/img/site/ are resized into a srcset at build time.
        test: /\.(jpe?g|png|webp)$/i,
        include: path.resolve(__dirname, "src/front/img/site"),
        use: {
          loader: "responsive-loader",
          options: {
            adapter: require("responsive-loader/sharp"),
            sizes: [480, 960, 1440, 1920],
            format: "webp",
            quality: 80,
            name: "img/[name]-[width]-[hash:8].[ext]",
            esModule: true,
          },
        },
      },
      {
        test: /\.(svg|png|jpe?g|webp|gif|ico)$/i,
        exclude: path.resolve(__dirname, "src/front/img/site"),
        type: "asset/resource",
        generator: { filename: "img/[name]-[hash:8][ext]" },
      },
    ],
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: "./template.html",
      favicon: "./src/front/img/favicon.svg",
      // Flask injects per-page SEO tags at the <!--SEO--> marker in production.
      minify: false,
    }),
    new CopyPlugin({
      patterns: [
        // Unhashed copies so Flask can use them as Open Graph share images.
        { from: "src/front/img/site", to: "img/site", globOptions: { ignore: ["**/*.md", "**/.gitkeep"] }, noErrorOnMissing: true },
        { from: "src/front/img/og-default.png", to: "img/og-default.png" },
      ],
    }),
  ],
  optimization: {
    runtimeChunk: "single",
    splitChunks: {
      chunks: "all",
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: "vendor",
          chunks: "initial",
          priority: 10,
        },
      },
    },
  },
  performance: { hints: false },
};
