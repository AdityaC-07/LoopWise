import { Trash2 } from 'lucide-react';
import { friendlyBinLabel, binColor } from '../utils/display';

interface BinCardProps {
  disposalBin: string;
  action: string;
}

export function BinCard({ disposalBin, action }: BinCardProps) {
  const color = binColor(disposalBin);
  const label = friendlyBinLabel(disposalBin);

  return (
    <div
      className="bin-card"
      style={{
        background: `color-mix(in srgb, ${color} 15%, var(--color-surface-1))`,
        borderColor: color,
      }}
    >
      <div
        style={{
          width: 48,
          height: 48,
          borderRadius: 'var(--radius-md)',
          background: `color-mix(in srgb, ${color} 25%, var(--color-surface-1))`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
        aria-hidden="true"
      >
        <Trash2 size={26} style={{ color }} />
      </div>
      <div>
        <div
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: 22,
            fontWeight: 600,
            color,
            lineHeight: 1.2,
            marginBottom: 4,
          }}
        >
          {label}
        </div>
        <div
          style={{
            fontSize: 15,
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
