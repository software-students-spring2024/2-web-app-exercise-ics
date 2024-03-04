/** @type {import('tailwindcss').Config} */
module.exports = {
  mode: "jit",
  content: ["./templates/*.html"],
  theme: {
    extend: {},
  },
  purge: ["./templates/**/*.html", "./static/**/*.{js,jsx,ts,tsx,vue}"],
  plugins: [],
};
