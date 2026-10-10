/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./ui/**/*.{html,js}",
    "./src/**/*.{py,html,js}"
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Instrument Sans"', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', '"Nirmala UI"', 'Gautami', 'Mangal', 'sans-serif'],
        display: ['"Instrument Sans"', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', '"Nirmala UI"', 'Gautami', 'Mangal', 'sans-serif'],
        mono: ['"DM Mono"', 'Consolas', 'Courier New', 'monospace']
      }
    }
  },
  safelist: [
    'hidden',
    'block',
    'flex',
    'grid',
    'active',
    'dark',
    'light',
    'border-amber-500/30',
    'border-amber-500/40',
    'text-amber-500',
    'bg-amber-500/10',
    'text-amber-700',
    'dark:text-amber-400',
    'bg-emerald-500/10',
    'text-emerald-500',
    'bg-blue-500/10',
    'text-blue-500'
  ],
  plugins: []
}
