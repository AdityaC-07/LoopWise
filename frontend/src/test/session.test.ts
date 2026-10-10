import { describe, it, expect, beforeEach } from 'vitest';
import { getSessionId } from '../utils/session';

describe('getSessionId', () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it('returns a valid UUID', () => {
    const id = getSessionId();
    expect(id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/);
  });

  it('returns the same ID on subsequent calls', () => {
    const id1 = getSessionId();
    const id2 = getSessionId();
    expect(id1).toBe(id2);
  });

  it('creates a new UUID when sessionStorage is cleared', () => {
    // Prime a session ID
    getSessionId();
    sessionStorage.clear();
    const freshId = getSessionId();
    expect(freshId).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/);
    expect(freshId.length).toBe(36);
  });
});
