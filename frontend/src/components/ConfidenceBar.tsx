import { confidenceTier, confidenceBarWidth } from '../utils/display';

interface ConfidenceBarProps {
  confidence: number;
  confidenceLabel: string;
}

export function ConfidenceBar({ confidence, confidenceLabel }: ConfidenceBarProps) {
  const tier = confidenceTier(confidence);
  const width = confidenceBarWidth(confidence);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
        <span
          style={{
            fontSize: '13px',
            fontWeight: 500,
            color: 'var(--color-text-secondary)',
          }}
        >
          How sure we are
        </span>
        <span
          style={{
            fontSize: '13px',
            fontWeight: 600,
            color:
              tier === 'high'
                ? 'var(--color-signal-good)'
                : tier === 'medium'
                ? 'var(--color-signal-warn)'
                : 'var(--color-signal-bad)',
          }}
        >
          {confidenceLabel}
        </span>
      </div>
      <div className="confidence-bar-track" role="meter" aria-label={`Confidence: ${confidenceLabel}`}>
        <div
          className={`confidence-bar-fill ${tier}`}
          style={{ width }}
          aria-hidden="true"
        />
      </div>
    </div>
  );
}
