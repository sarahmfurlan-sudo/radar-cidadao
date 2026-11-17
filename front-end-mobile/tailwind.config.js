/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        civic: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          500: '#0284c7',
          600: '#0369a1',
          700: '#075985',
          800: '#0c4a6e',
          900: '#0f172a',
          950: '#020617',
        },
        risk: {
          low: '#10b981',      // Verde normal
          moderate: '#f59e0b', // Amarelo atenção
          high: '#f97316',     // Laranja alerta
          critical: '#ef4444', // Vermelho emergência
        }
      }
    },
  },
  plugins: [],
}

