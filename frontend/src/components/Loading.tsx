interface LoadingDotsProps {
  label?: string;
}

export function LoadingDots({ label = 'Loading…' }: LoadingDotsProps) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 16,
        padding: '48px 24px',
      }}
      role="status"
      aria-live="polite"
    >
      <div className="loading-dots" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
      <span
        style={{
          fontSize: '15px',
          color: 'var(--color-text-secondary)',
        }}
      >
        {label}
      </span>
    </div>
  );
}

interface SkeletonProps {
  height?: number | string;
  width?: number | string;
  style?: React.CSSProperties;
}

export function Skeleton({ height = 20, width = '100%', style }: SkeletonProps) {
  return (
    <div
      className="skeleton"
      style={{ height, width, ...style }}
      aria-hidden="true"
    />
  );
}

export function ChartSkeleton() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <Skeleton height={8} width="60%" />
      <Skeleton height={180} />
      <Skeleton height={8} width="40%" />
    </div>
  );
}
