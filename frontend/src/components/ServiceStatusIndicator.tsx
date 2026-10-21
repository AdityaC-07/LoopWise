/** What /api/v1/health reports about the ONNX classifier. */
export type ClassifierStatus = 'ready' | 'unavailable' | 'unknown';

interface ServiceStatusIndicatorProps {
  status: ClassifierStatus;
}

/**
 * Top-bar indicator reflecting the ACTUAL classifier readiness reported by the
 * backend health endpoint. There is no hardcoded "live"/"demo" flag: the
 * backend tells us whether the ONNX model loaded, and we render exactly that.
 */
export function ServiceStatusIndicator({ status }: ServiceStatusIndicatorProps) {
  if (status === 'unknown') return null;

  const ready = status === 'ready';
  const label = ready ? 'Image recognition ready' : 'Image recognition unavailable';

  return (
    <span
      className="service-status-indicator"
      data-status={ready ? 'ready' : 'unavailable'}
      role="status"
      aria-label={ready
        ? 'Image recognition is available'
        : 'Image recognition is temporarily unavailable'}
      title={ready
        ? 'Photos are classified by the live vision model.'
        : 'The classification service is down. Please try again shortly.'}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
      }}
    >
      <span className="service-status-dot" aria-hidden="true" />
      {label}
    </span>
  );
}
