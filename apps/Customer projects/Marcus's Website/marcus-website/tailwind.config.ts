import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Elbey Projects brand colors
        primary: "#c62828", // Red accent
        background: "#000000", // Black background
        foreground: "#faf7f2", // Cream/ivory text
      },
    },
  },
  plugins: [],
};

export default config;
