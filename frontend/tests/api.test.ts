import { describe, it, expect } from 'vitest';
import { API_BASE_URL } from '../lib/api';

describe('NoteIQ API Client Config', () => {
  it('has a default or environment base URL', () => {
    expect(API_BASE_URL).toBeDefined();
    expect(typeof API_BASE_URL).toBe('string');
  });
});
