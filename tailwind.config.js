/**
 * Static Tailwind build configuration for eesti.chat.
 * Regenerate with: npx -y tailwindcss@3 -c tailwind.config.js -i tailwind.input.css -o static/tw.css --minify
 */
module.exports = {
  content: [
    'main.py',
    'components/**/*.py',
    'pages/**/*.py',
    'chat/**/*.py',
    'admin/**/*.py',
    'static/**/*.js',
    'static/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        blue: '#0030DE',
        'blue-deep': '#000087',
        'blue-ice': '#CEE2FD',
        ink: {
          DEFAULT: '#0F172A',
          2: '#3D4B5E',
          3: '#64748B',
        },
        line: '#CBD5E1',
        'bg-alt': '#F1F5F9',
        surface: '#FFFFFF',
      },
      fontFamily: {
        display: ['AinoHeadline', 'Verdana', 'system-ui', 'sans-serif'],
        sans: ['Aino', 'Verdana', 'system-ui', 'sans-serif'],
      },
    },
  },
};
