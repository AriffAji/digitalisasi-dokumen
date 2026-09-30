/** @type {import('tailwindcss').Config} */
export default {
  content: ["./templates/**/*.html"],
  theme: {
    extend: {
      colors: {
        hijau: {
          DEFAULT: "#205A28",
          50: "#f0f7f1",
          100: "#d9ecdb",
          200: "#b5d9b9",
          300: "#84be8b",
          400: "#519d5a",
          500: "#2f7d39",
          600: "#205A28",
          700: "#1a4820",
          800: "#163a1b",
          900: "#122f17",
        },
        merah: {
          DEFAULT: "#C72B32",
          50: "#fef2f2",
          100: "#fde3e4",
          200: "#fbcacc",
          300: "#f7a4a7",
          400: "#f17075",
          500: "#e74248",
          600: "#d12a30",
          700: "#b82229",
          800: "#a01d23",
          900: "#871920",
        },
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', "sans-serif"],
      },
    },
  },
  plugins: [require("flowbite/plugin")],
};
