import type { Material } from '../types/api';

/** Map a disposal_bin enum value to a friendly display label */
export function friendlyBinLabel(bin: string): string {
  const map: Record<string, string> = {
    wet: 'Green Wet Waste Bin',
    dry: 'Blue Dry Waste Bin',
    hazardous: 'Red Hazardous Bin',
    ewaste: 'E-Waste Drop-off',
    reject: 'Cannot be accepted',
    rejected: 'Check local waste rules',
    unknown: 'Check local waste rules',
    // backend may return differently cased
    'wet_waste': 'Green Wet Waste Bin',
    'dry_waste': 'Blue Dry Waste Bin',
    'e_waste': 'E-Waste Drop-off',
  };
  return map[bin.toLowerCase()] ?? bin;
}

/** Map a bin value to its CSS color token */
export function binColor(bin: string): string {
  const map: Record<string, string> = {
    wet: 'var(--color-bin-wet)',
    dry: 'var(--color-bin-dry)',
    hazardous: 'var(--color-bin-hazardous)',
    ewaste: 'var(--color-bin-ewaste)',
    reject: 'var(--color-bin-rejected)',
    rejected: 'var(--color-bin-rejected)',
    unknown: 'var(--color-bin-rejected)',
    wet_waste: 'var(--color-bin-wet)',
    dry_waste: 'var(--color-bin-dry)',
    e_waste: 'var(--color-bin-ewaste)',
  };
  return map[bin.toLowerCase()] ?? 'var(--color-text-tertiary)';
}

/** Map a material category to its CSS color token */
export function categoryColor(category: string): string {
  const map: Record<string, string> = {
    plastic: 'var(--color-mat-plastic)',
    paper: 'var(--color-mat-paper)',
    organic: 'var(--color-mat-organic)',
    glass: 'var(--color-mat-glass)',
    metal: 'var(--color-mat-metal)',
    ewaste: 'var(--color-mat-ewaste)',
    hazardous: 'var(--color-mat-hazardous)',
    composite: 'var(--color-mat-composite)',
    other: 'var(--color-mat-other)',
  };
  return map[category.toLowerCase()] ?? 'var(--color-mat-other)';
}

/** Plain-language label for recovery potential */
export function recoveryLabel(potential: string): string {
  const map: Record<string, string> = {
    high: 'Yes — high value material',
    medium: 'Possibly — if sorted correctly',
    low: 'Unlikely',
    none: 'No — cannot be recovered',
  };
  return map[potential.toLowerCase()] ?? potential;
}

/** Determine confidence tier */
export function confidenceTier(confidence: number): 'high' | 'medium' | 'low' {
  if (confidence >= 0.8) return 'high';
  if (confidence >= 0.55) return 'medium';
  return 'low';
}

/** Confidence bar width percentage */
export function confidenceBarWidth(confidence: number): string {
  const tier = confidenceTier(confidence);
  if (tier === 'high') return '100%';
  if (tier === 'medium') return '60%';
  return '30%';
}

/** Format a percentage from 0–1 for display */
export function formatPercent(val: number): string {
  return `${Math.round(val * 100)}%`;
}

/** Format a number with commas */
export function formatNumber(n: number): string {
  return n.toLocaleString('en-IN');
}

/** Get ward status label and CSS class from contamination rate */
export function wardStatus(contaminationRate: number): {
  label: string;
  cls: string;
} {
  if (contaminationRate < 0.1) return { label: 'Excellent', cls: 'excellent' };
  if (contaminationRate < 0.15) return { label: 'Good', cls: 'good' };
  if (contaminationRate < 0.2) return { label: 'Needs attention', cls: 'warn' };
  return { label: 'Needs work', cls: 'bad' };
}

/** Friendly ward name from ID */
export function friendlyWardName(wardId: string): string {
  const names: Record<string, string> = {
    'WD-DEMO-A': 'Ward A (Demo)',
    'WD-DEMO-B': 'Ward B (Demo)',
    'WD-DEMO-C': 'Ward C (Demo)',
    'WD-001': 'Ward 1',
    'WD-002': 'Ward 2',
    'WD-003': 'Ward 3',
  };
  return names[wardId] ?? wardId;
}

/** Friendly material class name (replace underscores, title-case) */
export function friendlyClassName(cls: string): string {
  return cls
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Convert image File to base64 data URL string (includes data: prefix) */
export function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsDataURL(file);
  });
}

/** Date helpers for analytics */
export function isoDate(d: Date): string {
  return d.toISOString().split('T')[0];
}

export function dateNDaysAgo(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return isoDate(d);
}

export function todayIso(): string {
  return isoDate(new Date());
}

/** Filter materials client-side */
export function filterMaterials(
  materials: Material[],
  search: string,
  category: string
): Material[] {
  const q = search.toLowerCase().trim();
  return materials.filter((m) => {
    const matchesSearch =
      !q ||
      m.name.toLowerCase().includes(q) ||
      m.category.toLowerCase().includes(q) ||
      (m.subcategory?.toLowerCase().includes(q) ?? false);
    const matchesCategory =
      !category || category === 'all' || m.category.toLowerCase() === category.toLowerCase();
    return matchesSearch && matchesCategory;
  });
}
