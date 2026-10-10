import { useEffect, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { ArrowLeft, CheckCircle, AlertTriangle, ChevronRight } from 'lucide-react';
import { BinCard } from '../components/BinCard';
import { ConfidenceBar } from '../components/ConfidenceBar';
import { RecoveryBar } from '../components/RecoveryBar';
import { MaterialBadge } from '../components/MaterialBadge';
import { ErrorMessage } from '../components/ErrorMessage';
import { submitFeedback, getMaterials } from '../api/client';
import { getSessionId } from '../utils/session';
import { confidenceTier, friendlyClassName, binColor } from '../utils/display';
import type { ClassifyResult, Material } from '../types/api';

type FeedbackState = 'idle' | 'confirming' | 'correcting' | 'submitted';

export default function ResultPage() {
  const { eventId } = useParams<{ eventId: string }>();
  const navigate = useNavigate();

  const [result, setResult] = useState<ClassifyResult | null>(null);
  const [demoMode, setDemoMode] = useState(true);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [feedbackState, setFeedbackState] = useState<FeedbackState>('idle');
  const [selectedCorrection, setSelectedCorrection] = useState('');
  const [feedbackError, setFeedbackError] = useState<string | null>(null);
  const [feedbackLoading, setFeedbackLoading] = useState(false);

  useEffect(() => {
    const stored = sessionStorage.getItem('loopwise_result');
    const storedDemo = sessionStorage.getItem('loopwise_demo_mode');
    if (stored) {
      setResult(JSON.parse(stored) as ClassifyResult);
      setDemoMode(storedDemo === 'true');
    }
  }, [eventId]);

  useEffect(() => {
    getMaterials().then((r) => setMaterials(r.data)).catch(() => {/* ignore */});
  }, []);

  async function handleConfirm() {
    if (!result || feedbackLoading) return;
    setFeedbackLoading(true);
    try {
      await submitFeedback({
        event_id: result.event_id,
        session_id: getSessionId(),
        feedback_type: 'confirmation',
      });
      setFeedbackState('submitted');
    } catch {
      setFeedbackError("We couldn't save your feedback. Please try again.");
    } finally {
      setFeedbackLoading(false);
    }
  }

  async function handleCorrection() {
    if (!result || feedbackLoading) return;
    setFeedbackLoading(true);
    try {
      await submitFeedback({
        event_id: result.event_id,
        session_id: getSessionId(),
        feedback_type: 'correction',
        corrected_class: selectedCorrection || undefined,
      });
      setFeedbackState('submitted');
    } catch {
      setFeedbackError("We couldn't save your correction. Please try again.");
    } finally {
      setFeedbackLoading(false);
    }
  }

  if (!result) {
    return (
      <div className="content-area" style={{ maxWidth: 560 }}>
        <div style={{ marginBottom: 16 }}>
          <Link to="/classify" className="btn btn-ghost" style={{ padding: '8px 0' }}>
            <ArrowLeft size={18} aria-hidden="true" /> Back to classify
          </Link>
        </div>
        <ErrorMessage
          message="We couldn't find the classification result. Please try again."
          code="NOT_FOUND"
          onRetry={() => navigate('/classify')}
        />
      </div>
    );
  }

  const tier = confidenceTier(result.confidence);

  return (
    <div className="content-area" style={{ maxWidth: 560 }}>
      {/* Back link */}
      <div style={{ marginBottom: 24 }}>
        <Link to="/classify" className="btn btn-ghost" style={{ padding: '8px 0', fontSize: 15 }}>
          <ArrowLeft size={18} aria-hidden="true" /> Back to classify
        </Link>
      </div>

      {/* Material name + badge */}
      <div style={{ marginBottom: 24 }}>
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 28,
            fontWeight: 600,
            color: 'var(--color-text-primary)',
            margin: '0 0 8px',
            lineHeight: 1.2,
          }}
        >
          {result.material.name || friendlyClassName(result.predicted_class)}
        </h1>
        <MaterialBadge category={result.material.category} />
        {demoMode && (
          <span
            style={{
              marginLeft: 8,
              fontSize: 11,
              fontWeight: 600,
              padding: '3px 8px',
              borderRadius: 'var(--radius-pill)',
              background: 'var(--color-amber-dim)',
              color: 'var(--color-amber)',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
            }}
          >
            Practice result
          </span>
        )}
      </div>

      {/* Uncertain demo result — photo could not be visually recognised */}
      {result.predicted_class === 'unknown' && (
        <div
          style={{
            background: 'var(--color-surface-2)',
            border: '1px solid var(--color-signal-warn)',
            borderRadius: 'var(--card-radius)',
            padding: 'var(--card-padding)',
            marginBottom: 24,
          }}
          role="alert"
        >
          <div style={{ fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 4 }}>
            Demo simulation — photo not recognised.
          </div>
          <div style={{ fontSize: 14, color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
            The demo cannot analyse photos, so this is not a verified image recognition result.
            Please describe the item in words or pick the closest material below, and check your
            local waste rules when unsure.
          </div>
        </div>
      )}

      {/* Low confidence warning + picker */}
      {tier === 'low' && feedbackState === 'idle' && (
        <div
          style={{
            background: 'var(--color-surface-2)',
            border: '1px solid var(--color-signal-warn)',
            borderRadius: 'var(--card-radius)',
            padding: 'var(--card-padding)',
            marginBottom: 24,
          }}
          role="alert"
        >
          <div
            style={{
              display: 'flex',
              gap: 10,
              alignItems: 'flex-start',
              marginBottom: 16,
            }}
          >
            <AlertTriangle size={18} style={{ color: 'var(--color-signal-warn)', flexShrink: 0, marginTop: 2 }} aria-hidden="true" />
            <div>
              <div style={{ fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 4 }}>
                We're not sure about this one.
              </div>
              <div style={{ fontSize: 14, color: 'var(--color-text-secondary)' }}>
                Please pick the closest match:
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {result.top3.map((item) => {
              const mat = materials.find((m) => m.name.toLowerCase().includes(item.class.toLowerCase().replace(/_/g, ' ').split(' ')[0]));
              const color = mat ? binColor(mat.disposal_bin) : 'var(--color-text-tertiary)';
              return (
                <label
                  key={item.class}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    padding: '12px',
                    borderRadius: 'var(--radius-md)',
                    border: `1px solid ${selectedCorrection === item.class ? 'var(--color-amber)' : 'var(--color-border)'}`,
                    background: selectedCorrection === item.class ? 'var(--color-surface-3)' : 'var(--color-surface-1)',
                    cursor: 'pointer',
                    transition: 'all 150ms ease',
                  }}
                >
                  <input
                    type="radio"
                    name="correction"
                    value={item.class}
                    checked={selectedCorrection === item.class}
                    onChange={() => setSelectedCorrection(item.class)}
                    style={{ accentColor: 'var(--color-amber)' }}
                  />
                  <span
                    style={{
                      width: 10,
                      height: 10,
                      borderRadius: '50%',
                      background: color,
                      flexShrink: 0,
                    }}
                    aria-hidden="true"
                  />
                  <span style={{ flex: 1, fontSize: 14, color: 'var(--color-text-primary)' }}>
                    {friendlyClassName(item.class)}
                  </span>
                  <span style={{ fontSize: 12, color: 'var(--color-text-tertiary)' }}>
                    {Math.round(item.confidence * 100)}%
                  </span>
                </label>
              );
            })}
            <label
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '12px',
                borderRadius: 'var(--radius-md)',
                border: `1px solid ${selectedCorrection === '__none__' ? 'var(--color-amber)' : 'var(--color-border)'}`,
                background: selectedCorrection === '__none__' ? 'var(--color-surface-3)' : 'var(--color-surface-1)',
                cursor: 'pointer',
              }}
            >
              <input
                type="radio"
                name="correction"
                value="__none__"
                checked={selectedCorrection === '__none__'}
                onChange={() => setSelectedCorrection('__none__')}
                style={{ accentColor: 'var(--color-amber)' }}
              />
              <span style={{ fontSize: 14, color: 'var(--color-text-secondary)' }}>
                None of these / I don't know
              </span>
            </label>
          </div>
          <button
            className="btn btn-primary"
            style={{ marginTop: 16, width: '100%' }}
            disabled={!selectedCorrection || feedbackLoading}
            onClick={handleCorrection}
          >
            Confirm my choice →
          </button>
        </div>
      )}

      {/* BinCard */}
      <div id="result-bin-card" style={{ marginBottom: 24 }}>
        <div className="section-label">Where it goes</div>
        <BinCard
          disposalBin={result.material.disposal_bin}
          action={result.guidance.action}
        />
      </div>

      {/* Confidence bar */}
      <div id="result-confidence-bar" style={{ marginBottom: 24 }}>
        <ConfidenceBar confidence={result.confidence} confidenceLabel={result.confidence_label} />
      </div>

      {/* Medium confidence — confirmation card */}
      {tier === 'medium' && feedbackState === 'idle' && (
        <div
          style={{
            background: 'var(--color-surface-2)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--card-radius)',
            padding: '16px 20px',
            marginBottom: 24,
          }}
          role="group"
          aria-label="Confirm classification"
        >
          <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start', marginBottom: 12 }}>
            <AlertTriangle size={16} style={{ color: 'var(--color-signal-warn)', flexShrink: 0, marginTop: 2 }} aria-hidden="true" />
            <div style={{ fontSize: 14, color: 'var(--color-text-secondary)' }}>
              We're not completely sure. Does this match what you have?
            </div>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button
              className="btn btn-primary"
              style={{ flex: 1, fontSize: 14 }}
              onClick={handleConfirm}
              disabled={feedbackLoading}
            >
              Yes, that's right
            </button>
            <button
              className="btn btn-secondary"
              style={{ flex: 1, fontSize: 14 }}
              onClick={() => setFeedbackState('correcting')}
              disabled={feedbackLoading}
            >
              No, it's different
            </button>
          </div>
        </div>
      )}

      {/* Recovery bar */}
      <div style={{ marginBottom: 24 }}>
        <RecoveryBar recoveryPotential={result.material.recovery_potential} />
      </div>

      {/* What happens next */}
      {result.material.next_life && (
        <div style={{ marginBottom: 24 }}>
          <div className="section-label">What happens next</div>
          <p style={{ fontSize: 15, color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.6 }}>
            {result.material.next_life}
          </p>
        </div>
      )}

      {/* How to sort it */}
      {(result.guidance.do.length > 0 || result.guidance.do_not.length > 0) && (
        <div style={{ marginBottom: 24 }}>
          <div className="section-label">How to sort it</div>
          <div className="card" style={{ padding: 16 }}>
            {result.guidance.do.map((item, i) => (
              <div key={i} style={{ display: 'flex', gap: 10, marginBottom: 8, fontSize: 14, color: 'var(--color-text-primary)' }}>
                <span style={{ color: 'var(--color-signal-good)', flexShrink: 0 }} aria-hidden="true">✓</span>
                <span>{item}</span>
              </div>
            ))}
            {result.guidance.do_not.map((item, i) => (
              <div key={i} style={{ display: 'flex', gap: 10, marginBottom: 8, fontSize: 14, color: 'var(--color-text-primary)' }}>
                <span style={{ color: 'var(--color-signal-bad)', flexShrink: 0 }} aria-hidden="true">✗</span>
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recovery channel */}
      {result.material.recovery_channel && (
        <div style={{ marginBottom: 24 }}>
          <div className="section-label">Recovery channel</div>
          <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', margin: 0 }}>
            {result.material.recovery_channel}
          </p>
        </div>
      )}

      {/* Contamination notes */}
      {result.material.contamination_notes && (
        <div style={{ marginBottom: 24 }}>
          <div className="section-label">Important notes</div>
          <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', margin: 0 }}>
            {result.material.contamination_notes}
          </p>
        </div>
      )}

      {/* Feedback section */}
      <hr className="divider" />

      {feedbackState === 'submitted' ? (
        <div
          style={{
            background: 'var(--color-surface-2)',
            border: '1px solid var(--color-signal-good)',
            borderRadius: 'var(--card-radius)',
            padding: 20,
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
            marginBottom: 16,
          }}
          role="status"
          aria-live="polite"
        >
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <CheckCircle size={20} style={{ color: 'var(--color-signal-good)' }} aria-hidden="true" />
            <span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>
              Thanks for the correction.
            </span>
          </div>
          <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', margin: 0 }}>
            Your feedback helps LoopWise get better for everyone in your ward.
          </p>
          <Link to="/classify" className="btn btn-primary" style={{ textAlign: 'center' }}>
            Classify another item →
          </Link>
        </div>
      ) : feedbackState === 'correcting' ? (
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 12 }}>
            What should it be?
          </div>
          {feedbackError && (
            <div style={{ marginBottom: 12 }}>
              <ErrorMessage message={feedbackError} />
            </div>
          )}
          <input
            type="text"
            className="input-field"
            placeholder='e.g. "paper" or "organic food waste"'
            value={selectedCorrection}
            onChange={(e) => setSelectedCorrection(e.target.value)}
            style={{ marginBottom: 12 }}
            aria-label="Enter the correct material class"
          />
          <div style={{ display: 'flex', gap: 10 }}>
            <button
              className="btn btn-secondary"
              onClick={() => setFeedbackState('idle')}
              disabled={feedbackLoading}
            >
              Cancel
            </button>
            <button
              className="btn btn-primary"
              disabled={!selectedCorrection.trim() || feedbackLoading}
              onClick={handleCorrection}
            >
              Save correction
            </button>
          </div>
        </div>
      ) : (
        tier !== 'low' && (
          <button
            id="result-feedback-btn"
            className="btn btn-ghost"
            onClick={() => setFeedbackState('correcting')}
            style={{ fontSize: 14 }}
          >
            <ChevronRight size={16} aria-hidden="true" />
            This doesn't look right
          </button>
        )
      )}
    </div>
  );
}
