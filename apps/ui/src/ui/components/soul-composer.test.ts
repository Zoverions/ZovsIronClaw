import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SoulComposer } from './soul-composer.js';

describe('SoulComposer', () => {
  beforeEach(() => {
    // Mock global fetch
    global.fetch = vi.fn();
  });

  it('initializes with default values', () => {
    const el = new SoulComposer();
    expect(el.baseSoul).toBe('Architect');
    expect(el.blendSouls).toEqual([]);
    expect(el.blendWeights).toEqual({});
  });

  it('fetches souls and updates state', async () => {
    const mockSouls = {
        souls: ['Architect', 'Stoic'],
        details: {
            'Architect': { name: 'Architect', description: 'Base' },
            'Stoic': { name: 'Stoic', description: 'Calm' }
        }
    };

    (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockSouls
    });

    const el = new SoulComposer();
    await el.fetchSouls();

    expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/v1/soul/list');
    expect(el.souls).toEqual(['Architect', 'Stoic']);
    expect(el.details).toEqual(mockSouls.details);
  });
});
