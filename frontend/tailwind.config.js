/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#060b18",
          900: "#0b152b",
          850: "#101e3d",
          800: "#162850",
          700: "#1f386e",
          600: "#2b4c92",
        },
        gold: {
          300: "#f0d59e",
          400: "#e5c07b",
          500: "#d19a40",
          600: "#b5802a",
        },
        slate: {
          850: "#172033",
          900: "#0f172a",
        },
      },
      fontFamily: {
        sans: ["'Work Sans'", "'Montserrat'", "system-ui", "sans-serif"],
        heading: ["'Montserrat'", "'Work Sans'", "sans-serif"],
        condensed: ["'Barlow Condensed'", "sans-serif"],
        display: ["'Momo Trust Display'", "'Montserrat'", "sans-serif"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in": "fadeIn 0.25s ease-out forwards",
        "slide-left": "slideLeft 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideLeft: {
          "0%": { transform: "translateX(100%)" },
          "100%": { transform: "translateX(0)" },
        },
      },
    },
  },
  plugins: [],
};
