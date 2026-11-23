/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: { extend: { colors: { midnight: "#090B18", panel: "#11172A", violet: "#A855F7", electric: "#397BFF", cyan: "#26E5E1" }, fontFamily: { sans: ["Inter", "ui-sans-serif", "system-ui"] } } },
  plugins: [],
};