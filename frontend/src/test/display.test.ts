import { describe, it, expect } from 'vitest';
import {
  friendlyBinLabel,
  binColor,
  recoveryLabel,
  confidenceTier,
  confidenceBarWidth,
  formatPercent,
  formatNumber,
  wardStatus,
  friendlyClassName,
  filterMaterials,
} from '../utils/display';
import type { Material } from '../types/api';

describe('friendlyBinLabel', () => {
  it('maps wet to green bin label', () => {
    expect(friendlyBinLabel('wet')).toBe('Green Wet Waste Bin');
  });
  it('maps dry to blue bin label', () => {
    expect(friendlyBinLabel('dry')).toBe('Blue Dry Waste Bin');
  });
  it('maps hazardous correctly', () => {
    expect(friendlyBinLabel('hazardous')).toBe('Red Hazardous Bin');
  });
  it('maps ewaste correctly', () => {
    expect(friendlyBinLabel('ewaste')).toBe('E-Waste Drop-off');
  });
  it('maps reject correctly', () => {
    expect(friendlyBinLabel('reject')).toBe('Cannot be accepted');
  });
  it('handles underscore variants', () => {
    expect(friendlyBinLabel('wet_waste')).toBe('Green Wet Waste Bin');
    expect(friendlyBinLabel('dry_waste')).toBe('Blue Dry Waste Bin');
  });
  it('returns raw value for unknown bin', () => {
    expect(friendlyBinLabel('unknown_bin')).toBe('unknown_bin');
  });
});

describe('binColor', () => {
  it('returns wet color token for wet', () => {
    expect(binColor('wet')).toBe('var(--color-bin-wet)');
  });
  it('returns dry color token for dry', () => {
    expect(binColor('dry')).toBe('var(--color-bin-dry)');
  });
  it('returns fallback for unknown', () => {
    expect(binColor('mystery')).toBe('var(--color-text-tertiary)');
  });
});

describe('recoveryLabel', () => {
  it('maps high correctly', () => {
    expect(recoveryLabel('high')).toBe('Yes — high value material');
  });
  it('maps medium correctly', () => {
    expect(recoveryLabel('medium')).toBe('Possibly — if sorted correctly');
  });
  it('maps none correctly', () => {
    expect(recoveryLabel('none')).toBe('No — cannot be recovered');
  });
});

describe('confidenceTier', () => {
  it('returns high for 0.9', () => {
    expect(confidenceTier(0.9)).toBe('high');
  });
  it('returns high for 0.8', () => {
    expect(confidenceTier(0.8)).toBe('high');
  });
  it('returns medium for 0.7', () => {
    expect(confidenceTier(0.7)).toBe('medium');
  });
  it('returns medium for 0.55', () => {
    expect(confidenceTier(0.55)).toBe('medium');
  });
  it('returns low for 0.5', () => {
    expect(confidenceTier(0.5)).toBe('low');
  });
  it('returns low for 0', () => {
    expect(confidenceTier(0)).toBe('low');
  });
});

describe('confidenceBarWidth', () => {
  it('returns 100% for high confidence', () => {
    expect(confidenceBarWidth(0.85)).toBe('100%');
  });
  it('returns 60% for medium confidence', () => {
    expect(confidenceBarWidth(0.65)).toBe('60%');
  });
  it('returns 30% for low confidence', () => {
    expect(confidenceBarWidth(0.3)).toBe('30%');
  });
});

describe('formatPercent', () => {
  it('formats 0.18 as 18%', () => {
    expect(formatPercent(0.18)).toBe('18%');
  });
  it('formats 1.0 as 100%', () => {
    expect(formatPercent(1.0)).toBe('100%');
  });
  it('formats 0 as 0%', () => {
    expect(formatPercent(0)).toBe('0%');
  });
});

describe('formatNumber', () => {
  it('formats 1423 with locale separator', () => {
    // en-IN uses commas too, value should contain digits
    const result = formatNumber(1423);
    expect(result).toContain('1');
    expect(result).toContain('4');
    expect(result).toContain('2');
    expect(result).toContain('3');
  });
});

describe('wardStatus', () => {
  it('returns excellent for < 10%', () => {
    expect(wardStatus(0.05).label).toBe('Excellent');
  });
  it('returns good for 10-15%', () => {
    expect(wardStatus(0.12).label).toBe('Good');
  });
  it('returns needs attention for 15-20%', () => {
    expect(wardStatus(0.17).label).toBe('Needs attention');
  });
  it('returns needs work for > 20%', () => {
    expect(wardStatus(0.25).label).toBe('Needs work');
  });
});

describe('friendlyClassName', () => {
  it('converts underscores to spaces and title-cases', () => {
    expect(friendlyClassName('plastic_pet_bottle')).toBe('Plastic Pet Bottle');
  });
  it('handles single word', () => {
    expect(friendlyClassName('plastic')).toBe('Plastic');
  });
});

describe('filterMaterials', () => {
  const mockMaterials: Material[] = [
    {
      material_id: '1',
      name: 'PET Bottle',
      category: 'plastic',
      subcategory: 'PET',
      disposal_bin: 'dry',
      recovery_potential: 'high',
      next_life: 'Recycled into fibre',
      recovery_channel: 'Municipal',
      contamination_notes: 'Rinse before placing',
      icon_slug: 'pet_bottle',
      demo_seed: true,
    },
    {
      material_id: '2',
      name: 'Banana Peel',
      category: 'organic',
      subcategory: 'food_waste',
      disposal_bin: 'wet',
      recovery_potential: 'none',
      next_life: 'Composted',
      recovery_channel: 'Municipal composting',
      contamination_notes: '',
      icon_slug: 'banana_peel',
      demo_seed: true,
    },
  ];

  it('returns all when no filter', () => {
    expect(filterMaterials(mockMaterials, '', 'all')).toHaveLength(2);
  });
  it('filters by search term', () => {
    const result = filterMaterials(mockMaterials, 'bottle', 'all');
    expect(result).toHaveLength(1);
    expect(result[0].name).toBe('PET Bottle');
  });
  it('filters by category', () => {
    const result = filterMaterials(mockMaterials, '', 'organic');
    expect(result).toHaveLength(1);
    expect(result[0].category).toBe('organic');
  });
  it('returns empty when no match', () => {
    expect(filterMaterials(mockMaterials, 'zzz', 'all')).toHaveLength(0);
  });
});
