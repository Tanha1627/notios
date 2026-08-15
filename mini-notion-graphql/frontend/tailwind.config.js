/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#FAF9F6",
        ink: "#211D18",
        subink: "#6B6459",
        line: "#E4E0D8",
        surface: "#FFFFFF",
        pine: {
          50: "#EEF3F1",
          100: "#D3E0DC",
          300: "#7FA69D",
          500: "#2F5D57",
          600: "#254944",
          700: "#1B3733",
        },
        amber: {
          100: "#F4E4C1",
          500: "#B8842E",
          700: "#8A6222",
        },
        slate: {
          100: "#E7E9EA",
          500: "#7C8489",
        },
      },
      fontFamily: {
        display: ["'Fraunces'", "serif"],
        body: ["'Inter'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      borderRadius: {
        card: "10px",
      },
      boxShadow: {
        soft: "0 1px 2px rgba(33,29,24,0.06), 0 1px 1px rgba(33,29,24,0.04)",
        panel: "0 4px 24px rgba(33,29,24,0.08)",
      },
    },
  },
  plugins: [],
};
