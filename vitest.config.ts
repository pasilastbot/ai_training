import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./vitest.setup.ts'],
    coverage: {
      reporter: ['text', 'json', 'html'],
      include: ['public/**/*.{js,ts}'],
      exclude: ['**/*.test.{js,ts}', '**/node_modules/**']
    }
  }
});
