// envName follows NODE_ENV (set by webpack.dev.js / webpack.prod.js).
module.exports = (api) => {
  const dev = api.env("development");
  return {
    presets: [
      "@babel/preset-env",
      ["@babel/preset-react", { runtime: "automatic", development: dev }],
    ],
  };
};
