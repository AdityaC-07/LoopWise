import { recoveryLabel } from '../utils/display';

interface RecoveryBarProps {
  recoveryPotential: string;
}

const tierConfig = {
  high:   { label: 'Yes — high value material',      color: 'var(--color-signal-good)', width: '100%' },
  medium: { label: 'Possibly — if sorted correctly',  color: 'var(--color-signal-warn)', width: '60%' },
  low:    { label: 'Unlikely',                        color: 'var(--color-signal-bad)',  width: '30%' },
  none:   { label: 'No — cannot be recovered',        color: 'var(--color-text-tertiary)', width: '5%' },
};

function getTier(potential: string) {
  const key = potential.toLowerCase() as keyof typeof tierConfig;
  return tierConfig[key] ?? { label: recoveryLabel(potential), color: 'var(--color-text-tertiary)', width: '10%' };
}

export function RecoveryBar({ recoveryPotential }: RecoveryBarProps) {
  const config = getTier(recoveryPotential);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
        <span
          style={{ fontSize: '13px', fontWeight: 500, color: 'var(--color-text-secondary)' }}
        >
          Can this be recycled?
        </span>
        <span style={{ fontSize: '13px', fontWeight: 600, color: config.color }}>
          {config.label}
        </span>
      </div>
      <div
        className="confidence-bar-track"
        role="meter"
        aria-label={`Recycling potential: ${config.label}`}
      >
        <div
          style={{
            height: '100%',
            width: config.width,
            borderRadius: 'var(--radius-pill)',
            background: config.color,
            transition: 'width 400ms ease-out',
          }}
          aria-hidden="true"
        />
      </div>
    </div>
  );
}
