/* eslint-env node */
module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: ["eslint:recommended", "plugin:react-hooks/recommended"],
  parserOptions: { ecmaVersion: "latest", sourceType: "module" },
  ignorePatterns: ["dist", "build"],
  rules: {
    "react-refresh/only-export-components": ["warn", { allowConstantExport: true }]
  },
  plugins: ["react-refresh"]
};
