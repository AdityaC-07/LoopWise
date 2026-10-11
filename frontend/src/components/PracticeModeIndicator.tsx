import { Info } from 'lucide-react';
import { useState } from 'react';

interface PracticeModeIndicatorProps {
  demoMode?: boolean;
}

export function PracticeModeIndicator({ demoMode }: PracticeModeIndicatorProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  if (demoMode !== true) return null;

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <button
        className="practice-mode-indicator"
        onClick={() => setShowTooltip((v) => !v)}
        aria-label="Practice mode — click for more information"
        aria-expanded={showTooltip}
      >
        Practice Mode — not live data
      </button>
      {showTooltip && (
        <div
          role="tooltip"
          style={{
            position: 'absolute',
            top: 'calc(100% + 8px)',
            right: 0,
            background: 'var(--color-surface-1)',
            border: '1px solid var(--color-border-accent)',
            borderRadius: 'var(--radius-md)',
            padding: '10px 14px',
            fontSize: '13px',
            color: 'var(--color-text-secondary)',
            whiteSpace: 'nowrap',
            boxShadow: 'var(--shadow-md)',
            zIndex: 300,
          }}
        >
          This is a training version using test data. Results are not live.
        </div>
      )}
      {showTooltip && (
        <div
          style={{ position: 'fixed', inset: 0, zIndex: 299 }}
          onClick={() => setShowTooltip(false)}
          aria-hidden="true"
        />
      )}
    </div>
  );
}

export function PracticeModeTooltip({ demoMode }: PracticeModeIndicatorProps) {
  if (demoMode !== true) return null;

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '10px',
        background: 'var(--color-amber-dim)',
        border: '1px solid var(--color-amber)',
        borderRadius: 'var(--radius-md)',
        padding: '10px 14px',
        fontSize: '13px',
        color: 'var(--color-amber)',
        marginBottom: '16px',
      }}
      role="status"
      aria-label="Practice mode active"
    >
      <Info size={16} style={{ flexShrink: 0, marginTop: 2 }} aria-hidden="true" />
      <span>
        <strong>Practice Mode</strong> — demo simulation, not a live vision model. Photos alone cannot be recognised here; add a description for a closer match. Results are illustrative only.
      </span>
    </div>
  );
}
