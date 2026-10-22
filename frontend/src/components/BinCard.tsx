import { Trash2 } from 'lucide-react';
import { friendlyBinLabel, binColor } from '../utils/display';

interface BinCardProps {
  disposalBin: string;
  action: string;
  /** Render with reduced visual weight (smaller type, icon, padding) */
  compact?: boolean;
}

export function BinCard({ disposalBin, action, compact = false }: BinCardProps) {
  const color = binColor(disposalBin);
  const label = friendlyBinLabel(disposalBin);

  return (
    <div
      className="bin-card"
      style={{
        background: `color-mix(in srgb, ${color} ${compact ? 8 : 15}%, var(--color-surface-1))`,
        borderColor: color,
        borderWidth: compact ? 1 : 2,
        padding: compact ? 'var(--space-4)' : undefined,
        gap: compact ? 'var(--space-3)' : undefined,
      }}
    >
      <div
        style={{
          width: compact ? 36 : 48,
          height: compact ? 36 : 48,
          borderRadius: 'var(--radius-md)',
          background: `color-mix(in srgb, ${color} ${compact ? 14 : 25}%, var(--color-surface-1))`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
        aria-hidden="true"
      >
        <Trash2 size={compact ? 18 : 26} style={{ color, opacity: compact ? 0.85 : 1 }} />
      </div>
      <div>
        <div
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: compact ? 16 : 22,
            fontWeight: 600,
            color,
            lineHeight: 1.3,
            marginBottom: compact ? 2 : 4,
          }}
        >
          {label}
        </div>
        <div
          style={{
            fontSize: compact ? 14 : 15,
            color: 'var(--color-text-secondary)',
            lineHeight: 1.5,
          }}
        >
          {action}
        </div>
      </div>
    </div>
  );
}
