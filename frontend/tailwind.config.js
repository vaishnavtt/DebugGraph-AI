/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Warm ivory and porcelain canvas
        ivory: {
          50: '#FDFCF9',
          100: '#FAF7F0',
          200: '#F4EFE6',
          300: '#EBE3D3',
          400: '#DED2BA',
          500: '#C8B796',
          600: '#A4916E',
          700: '#7F6E4E',
          800: '#5C4E34',
          900: '#3D3320',
        },
        // Deep midnight obsidian for dramatic contrast sections
        midnight: {
          950: '#060911',
          900: '#0A0E1A',
          850: '#0F172A',
          800: '#141E33',
          750: '#192640',
          700: '#1E2F52',
          600: '#283E6B',
          500: '#3B5996',
        },
        // Jacob & Co. inspired champagne gold accents
        gold: {
          50: '#FBF8F0',
          100: '#F5EED9',
          200: '#EBDBB0',
          300: '#DFC482',
          400: '#D4B15C',
          500: '#C5A059', // Core champagne gold
          600: '#A8823B',
          700: '#846329',
          800: '#644A1E',
          900: '#463313',
        },
        // Electric cobalt blue
        electric: {
          50: '#EEF5FF',
          100: '#D9EBFF',
          200: '#B8DBFF',
          300: '#85C2FF',
          400: '#479FFF',
          500: '#0066FF', // Core electric blue
          600: '#0052CC',
          700: '#003D99',
          800: '#002B6B',
          900: '#001A42',
        },
        brand: {
          50: '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
          950: '#1e1b4b',
        },
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
        display: ['"Plus Jakarta Sans"', 'sans-serif'],
      },
      boxShadow: {
        'soft': '0 2px 10px -2px rgba(15, 23, 42, 0.04), 0 1px 3px -1px rgba(15, 23, 42, 0.02)',
        'card': '0 4px 24px -2px rgba(15, 23, 42, 0.05), 0 2px 8px -1px rgba(15, 23, 42, 0.02)',
        'card-hover': '0 16px 36px -6px rgba(15, 23, 42, 0.09), 0 6px 14px -2px rgba(15, 23, 42, 0.04)',
        // Tactile 3D button shadows
        'tactile-primary': '0 3px 0 #0044B3, 0 6px 16px rgba(0, 102, 255, 0.35)',
        'tactile-gold': '0 3px 0 #846329, 0 6px 18px rgba(197, 160, 89, 0.35)',
        'tactile-dark': '0 3px 0 #000000, 0 6px 16px rgba(0, 0, 0, 0.25)',
        'tactile-surface': '0 2px 0 #E2E8F0, 0 4px 12px rgba(15, 23, 42, 0.04)',
        'glass-luxury': '0 8px 32px 0 rgba(15, 23, 42, 0.06), inset 0 1px 0 0 rgba(255, 255, 255, 0.8)',
        'glow-electric': '0 0 24px -4px rgba(0, 102, 255, 0.45)',
        'glow-gold': '0 0 24px -4px rgba(197, 160, 89, 0.45)',
      },
      borderRadius: {
        'xl': '0.875rem',
        '2xl': '1rem',
        '3xl': '1.5rem',
        '4xl': '2rem',
      },
      animation: {
        'float-slow': 'floatSlow 8s ease-in-out infinite',
        'float-medium': 'floatMedium 6s ease-in-out infinite',
        'float-reverse': 'floatReverse 10s ease-in-out infinite',
        'pulse-subtle': 'pulseSubtle 3s ease-in-out infinite',
        'shimmer': 'shimmer 2.5s linear infinite',
      },
      keyframes: {
        floatSlow: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-8px)' },
        },
        floatMedium: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-5px)' },
        },
        floatReverse: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(7px)' },
        },
        pulseSubtle: {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.8', transform: 'scale(0.98)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
    },
  },
  plugins: [],
}
