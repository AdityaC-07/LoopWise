import { AlertCircle, WifiOff } from 'lucide-react';

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
  code?: string;
}

export function ErrorMessage({ message, onRetry, code }: ErrorMessageProps) {
  const icon = code === 'NETWORK_ERROR' ? (
    <WifiOff size={20} style={{ color: 'var(--color-signal-bad)' }} aria-hidden="true" />
  ) : (
    <AlertCircle size={20} style={{ color: 'var(--color-signal-bad)' }} aria-hidden="true" />
  );

  return (
    <div
      role="alert"
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: 12,
        background: 'var(--color-signal-bad-dim)',
        border: '1px solid var(--color-signal-bad)',
        borderRadius: 'var(--radius-md)',
        padding: '14px 16px',
        fontSize: '14px',
        color: 'var(--color-text-primary)',
      }}
    >
      {icon}
      <div style={{ flex: 1 }}>
        <div>{message}</div>
        {onRetry && (
          <button
            className="btn-ghost"
            onClick={onRetry}
            style={{ marginTop: 8, fontSize: '13px', padding: '4px 0', color: 'var(--color-amber)' }}
          >
            Try again
          </button>
        )}
      </div>
    </div>
  );
}

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  body: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon, title, body, action }: EmptyStateProps) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        textAlign: 'center',
        padding: '64px 24px',
        gap: 16,
      }}
      role="status"
    >
      {icon && (
        <div style={{ color: 'var(--color-amber)', marginBottom: 8 }} aria-hidden="true">
          {icon}
        </div>
      )}
      <h2
        style={{
          fontFamily: 'var(--font-display)',
          fontSize: 22,
          fontWeight: 600,
          color: 'var(--color-text-primary)',
          margin: 0,
        }}
      >
        {title}
      </h2>
      <p style={{ fontSize: 15, color: 'var(--color-text-secondary)', margin: 0, maxWidth: 360 }}>
        {body}
      </p>
      {action}
    </div>
  );
}
