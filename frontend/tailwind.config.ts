export default {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-family)', 'Inter', 'sans-serif'],
      },
      colors: {
        primary: {
          DEFAULT: 'var(--color-primary, #3b82f6)',
          hover: 'var(--color-primary-hover, #2563eb)',
        },
        surface: {
          DEFAULT: 'var(--color-bg, #0f172a)',
          card: 'var(--color-card, #1e293b)',
          hover: 'var(--color-card-hover, #263347)',
        },
        border: {
          DEFAULT: 'var(--color-border, #334155)',
          light: 'var(--color-border-light, #475569)',
        },
        text: {
          primary: 'var(--color-text-primary, #f1f5f9)',
          secondary: 'var(--color-text-secondary, #94a3b8)',
        },
      },
    },
  },
  plugins: [require('@tailwindcss/forms')],
}
