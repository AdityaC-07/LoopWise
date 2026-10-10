interface StatusLightProps {
  contaminationRate: number;
  showLabel?: boolean;
}

export function wardStatusInfo(rate: number) {
  if (rate < 0.1) return { label: 'Excellent', cls: 'excellent' };
  if (rate < 0.15) return { label: 'Good', cls: 'good' };
  if (rate < 0.2) return { label: 'Needs attention', cls: 'warn' };
  return { label: 'Needs work', cls: 'bad' };
}

export function StatusLight({ contaminationRate, showLabel = true }: StatusLightProps) {
  const { label, cls } = wardStatusInfo(contaminationRate);
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
      <span
        className={`status-light ${cls}`}
        role="img"
        aria-label={label}
      />
      {showLabel && (
        <span style={{ fontSize: '14px', color: 'var(--color-text-secondary)' }}>
          {label}
        </span>
      )}
    </span>
  );
}
