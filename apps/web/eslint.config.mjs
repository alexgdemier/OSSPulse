import tsParser from "@typescript-eslint/parser";
import nextPlugin from "@next/eslint-plugin-next";
import reactPlugin from "eslint-plugin-react";

export default [
  { ignores: [".next/**", "out/**", "build/**", "next-env.d.ts"] },
  {
    files: ["**/*.{js,jsx,ts,tsx}"],
    settings: { react: { version: "detect" } },
    languageOptions: {
      parser: tsParser,
      parserOptions: { ecmaFeatures: { jsx: true }, sourceType: "module", ecmaVersion: "latest" },
    },
    plugins: { "@next/next": nextPlugin, react: reactPlugin },
    rules: {
      ...nextPlugin.configs.recommended.rules,
      ...reactPlugin.configs.flat.recommended.rules,
      ...reactPlugin.configs.flat["jsx-runtime"].rules,
    },
  },
];
