import { expect, afterEach, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

// Cleanup after each test (manual DOM cleanup)
afterEach(() => {
  document.body.innerHTML = '';
  document.documentElement.removeAttribute('style');
});

// Mock fetch globally
global.fetch = vi.fn();

// Add custom matchers
expect.extend({});
