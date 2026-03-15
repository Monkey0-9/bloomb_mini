/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'void': 'var(--void)',
        'surface-0': 'var(--surface-0)',
        'surface-1': 'var(--surface-1)',
        'surface-2': 'var(--surface-2)',
        'surface-3': 'var(--surface-3)',
        'surface-4': 'var(--surface-4)',
        'bull': 'var(--bull)',
        'bear': 'var(--bear)',
        'neutral': 'var(--neutral)',
        'accent-1': 'var(--accent-1)',
        'accent-2': 'var(--accent-2)',
        'accent-3': 'var(--accent-3)',
      },
      fontFamily: {
        'display': ['"Bebas Neue"', 'sans-serif'],
        'mono': ['"IBM Plex Mono"', 'monospace'],
        'sans': ['"DM Sans"', 'sans-serif'],
        'serif': ['"Lora"', 'serif'],
      },
      fontSize: {
        '2xs': '9px',
        'xs': '10px',
        'sm': '11px',
        'base': '12px',
        'md': '13px',
        'lg': '14px',
        'xl': '16px',
        '2xl': '20px',
        '3xl': '24px',
        '4xl': '32px',
        'display': '48px',
      }
    },
  },
  plugins: [],
}
