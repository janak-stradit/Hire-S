/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["JetBrains Mono", "Menlo", "monospace"],
      },
      fontSize: {
        "2xs": ["0.75rem",    { lineHeight: "1.125rem", letterSpacing: "0.02em"  }],
        xs:    ["0.8125rem",  { lineHeight: "1.25rem",  letterSpacing: "0.01em"  }],
        sm:    ["0.9375rem",  { lineHeight: "1.5rem",   letterSpacing: "0em"     }],
        base:  ["1rem",       { lineHeight: "1.625rem", letterSpacing: "-0.011em"}],
        md:    ["1.0625rem",  { lineHeight: "1.625rem", letterSpacing: "-0.013em"}],
        lg:    ["1.1875rem",  { lineHeight: "1.75rem",  letterSpacing: "-0.016em"}],
        xl:    ["1.375rem",   { lineHeight: "1.875rem", letterSpacing: "-0.018em"}],
        "2xl": ["1.625rem",   { lineHeight: "2.125rem", letterSpacing: "-0.022em"}],
        "3xl": ["2rem",       { lineHeight: "2.5rem",   letterSpacing: "-0.026em"}],
        "4xl": ["2.5rem",     { lineHeight: "3rem",     letterSpacing: "-0.032em"}],
      },
      colors: {
        brand: {
          50:  "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e40af",
          900: "#1e3a8a",
        },
        sidebar: {
          bg:     "#0f172a",
          hover:  "#1e293b",
          border: "#1e293b",
        },
      },
      boxShadow: {
        "card-xs":  "0 1px 2px 0 rgb(0 0 0 / 0.05)",
        "card-sm":  "0 1px 3px 0 rgb(0 0 0 / 0.08), 0 1px 2px -1px rgb(0 0 0 / 0.06)",
        "card-md":  "0 4px 8px -2px rgb(0 0 0 / 0.08), 0 2px 4px -2px rgb(0 0 0 / 0.05)",
        "card-lg":  "0 12px 20px -4px rgb(0 0 0 / 0.10), 0 4px 8px -4px rgb(0 0 0 / 0.06)",
        "card-xl":  "0 24px 32px -6px rgb(0 0 0 / 0.12), 0 8px 12px -6px rgb(0 0 0 / 0.06)",
        "inner-sm": "inset 0 1px 2px 0 rgb(0 0 0 / 0.05)",
      },
      spacing: {
        "4.5": "1.125rem",
        "5.5": "1.375rem",
        "13":  "3.25rem",
        "15":  "3.75rem",
        "18":  "4.5rem",
      },
    },
  },
  plugins: [],
};
