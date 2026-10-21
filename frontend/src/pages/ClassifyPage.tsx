import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Camera, Upload, X, HelpCircle } from 'lucide-react';
import { classifyItem } from '../api/client';
import { getSessionId } from '../utils/session';
import { fileToBase64 } from '../utils/display';
import { ErrorMessage } from '../components/ErrorMessage';
import type { ApiError } from '../api/client';

const WARD_OPTIONS = [
  { id: '', label: 'No ward (optional)' },
  { id: 'WD-DEMO-A', label: 'Ward A (Demo)' },
  { id: 'WD-DEMO-B', label: 'Ward B (Demo)' },
  { id: 'WD-DEMO-C', label: 'Ward C (Demo)' },
  { id: 'WD-001', label: 'Ward 1' },
  { id: 'WD-002', label: 'Ward 2' },
  { id: 'WD-003', label: 'Ward 3' },
];

export default function ClassifyPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [description, setDescription] = useState('');
  const [wardId, setWardId] = useState('');
  const [consentImageUpload, setConsentImageUpload] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<{ code: string; message: string } | null>(null);
  const [dragging, setDragging] = useState(false);
  const [showConsentTooltip, setShowConsentTooltip] = useState(false);

  // A photo is required: classification runs on the image alone. The
  // description is optional context the user may add.
  const hasInput = !!imageFile;

  function handleFileSelect(file: File) {
    if (!file.type.startsWith('image/')) {
      setError({ code: 'UNSUPPORTED_FORMAT', message: "We couldn't read that file. Please use a JPEG or PNG photo." });
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setError({ code: 'IMAGE_TOO_LARGE', message: 'That photo is too large. Please try a smaller photo.' });
      return;
    }
    setError(null);
    setImageFile(file);
    const url = URL.createObjectURL(file);
    setImagePreview(url);
  }

  function handleFileInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFileSelect(file);
    e.target.value = '';
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFileSelect(file);
  }

  function removeImage() {
    setImageFile(null);
    if (imagePreview) {
      URL.revokeObjectURL(imagePreview);
      setImagePreview(null);
    }
  }

  async function handleSubmit() {
    if (!hasInput || loading) return;
    setLoading(true);
    setError(null);

    try {
      let imageB64: string | undefined;
      if (imageFile) {
        imageB64 = await fileToBase64(imageFile);
      }

      const result = await classifyItem({
        session_id: getSessionId(),
        input_type: imageFile ? 'image' : 'text',
        image_b64: imageB64,
        description: description.trim() || undefined,
        ward_id: wardId || undefined,
        consent: {
          image_upload: consentImageUpload,
          analytics: true,
          location: false,
        },
      });

      // Store result in sessionStorage for the result page
      sessionStorage.setItem('loopwise_result', JSON.stringify(result.data));
      navigate(`/result/${result.data.event_id}`);
    } catch (err) {
      const apiErr = err as ApiError;
      setError({ code: apiErr.code ?? 'UNKNOWN', message: apiErr.message });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="content-area" style={{ maxWidth: 560, paddingTop: 32 }}>
      <h1
        style={{
          fontFamily: 'var(--font-display)',
          fontSize: 28,
          fontWeight: 600,
          color: 'var(--color-text-primary)',
          margin: '0 0 8px',
        }}
      >
        Identify Waste
      </h1>
      <p style={{ fontSize: 15, color: 'var(--color-text-secondary)', margin: '0 0 24px' }}>
        Take a photo to find out which bin it belongs in. A description is optional, and
        helps when the photo is unclear.
      </p>

      {error && (
        <div style={{ marginBottom: 16 }}>
          <ErrorMessage message={error.message} code={error.code} onRetry={() => setError(null)} />
        </div>
      )}

      {/* Upload zone */}
      {!imagePreview ? (
        <div
          id="classify-upload-btn"
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
          aria-label="Upload a photo of the waste item"
          onKeyDown={(e) => e.key === 'Enter' && fileInputRef.current?.click()}
          style={{
            border: `2px dashed ${dragging ? 'var(--color-amber)' : 'var(--color-border-strong)'}`,
            borderRadius: 'var(--card-radius)',
            background: dragging ? 'var(--color-surface-3)' : 'var(--color-surface-2)',
            padding: '40px 24px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 12,
            cursor: 'pointer',
            transition: 'all 150ms ease',
            marginBottom: 24,
          }}
        >
          <div
            style={{
              width: 64,
              height: 64,
              borderRadius: '50%',
              background: 'var(--color-amber-dim)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
            aria-hidden="true"
          >
            <Camera size={28} style={{ color: 'var(--color-amber)' }} />
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 4 }}>
              Take a photo or upload
            </div>
            <div style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
              Drag and drop here, or click to browse
            </div>
            <div style={{ fontSize: 12, color: 'var(--color-text-tertiary)', marginTop: 4 }}>
              JPEG or PNG, up to 5 MB
            </div>
          </div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              color: 'var(--color-text-tertiary)',
              fontSize: 13,
            }}
          >
            <Upload size={14} aria-hidden="true" />
            <span>Browse files</span>
          </div>
        </div>
      ) : (
        <div
          style={{
            position: 'relative',
            borderRadius: 'var(--card-radius)',
            overflow: 'hidden',
            marginBottom: 24,
            border: '1px solid var(--color-border)',
          }}
        >
          <img
            src={imagePreview}
            alt="Preview of the uploaded waste item"
            style={{ width: '100%', maxHeight: 280, objectFit: 'cover', display: 'block' }}
          />
          <button
            onClick={removeImage}
            aria-label="Remove uploaded photo"
            style={{
              position: 'absolute',
              top: 8,
              right: 8,
              background: 'var(--color-surface-1)',
              border: '1px solid var(--color-border)',
              borderRadius: '50%',
              width: 32,
              height: 32,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              color: 'var(--color-text-secondary)',
            }}
          >
            <X size={16} />
          </button>
        </div>
      )}

      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        capture="environment"
        onChange={handleFileInputChange}
        style={{ display: 'none' }}
        aria-hidden="true"
      />

      {/* Divider */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          marginBottom: 20,
          color: 'var(--color-text-tertiary)',
          fontSize: 13,
        }}
      >
        <div style={{ flex: 1, borderTop: '1px solid var(--color-border)' }} />
        add a description (optional)
        <div style={{ flex: 1, borderTop: '1px solid var(--color-border)' }} />
      </div>

      {/* Description input */}
      <div style={{ marginBottom: 20 }}>
        <label
          htmlFor="classify-description"
          style={{
            display: 'block',
            fontSize: 13,
            fontWeight: 500,
            color: 'var(--color-text-secondary)',
            marginBottom: 6,
          }}
        >
          Describe the item (optional)
        </label>
        <textarea
          id="classify-description"
          className="input-field"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder='e.g. "plastic water bottle" or "old newspaper"'
          rows={3}
          style={{ resize: 'vertical', lineHeight: 1.5 }}
          aria-label="Describe the waste item"
        />
      </div>

      {/* Ward dropdown */}
      <div style={{ marginBottom: 20 }}>
        <label
          htmlFor="ward-select"
          style={{
            display: 'block',
            fontSize: 13,
            fontWeight: 500,
            color: 'var(--color-text-secondary)',
            marginBottom: 6,
          }}
        >
          Which ward? (optional)
        </label>
        <div style={{ position: 'relative' }}>
          <select
            id="ward-select"
            className="select-field"
            value={wardId}
            onChange={(e) => setWardId(e.target.value)}
          >
            {WARD_OPTIONS.map((w) => (
              <option key={w.id} value={w.id}>
                {w.label}
              </option>
            ))}
          </select>
          <div
            style={{
              position: 'absolute',
              right: 12,
              top: '50%',
              transform: 'translateY(-50%)',
              pointerEvents: 'none',
              color: 'var(--color-text-tertiary)',
            }}
            aria-hidden="true"
          >
            ▾
          </div>
        </div>
      </div>

      {/* Consent checkbox */}
      <div style={{ marginBottom: 24 }}>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={consentImageUpload}
            onChange={(e) => setConsentImageUpload(e.target.checked)}
          />
          <span>
            Save photo to help improve LoopWise.{' '}
            <button
              className="btn-ghost"
              onClick={() => setShowConsentTooltip((v) => !v)}
              aria-label="Privacy information about photo saving"
              style={{ fontSize: 13, padding: '0 2px', verticalAlign: 'middle', minWidth: 'unset' }}
            >
              <HelpCircle size={14} aria-hidden="true" />
            </button>
          </span>
        </label>
        {showConsentTooltip && (
          <div
            role="tooltip"
            style={{
              marginTop: 8,
              padding: '8px 12px',
              background: 'var(--color-surface-2)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              fontSize: 13,
              color: 'var(--color-text-secondary)',
            }}
          >
            Your photo will only be saved if you check this box.
          </div>
        )}
      </div>

      {/* Submit button */}
      {loading ? (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
            padding: '24px',
            background: 'var(--color-surface-2)',
            borderRadius: 'var(--card-radius)',
            border: '1px solid var(--color-border)',
          }}
          role="status"
          aria-live="polite"
        >
          <div className="loading-dots" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
          <span style={{ fontSize: 15, color: 'var(--color-text-secondary)' }}>
            Checking the item…
          </span>
        </div>
      ) : (
        <>
          <button
            className="btn btn-primary"
            style={{ width: '100%' }}
            disabled={!hasInput}
            onClick={handleSubmit}
            aria-disabled={!hasInput}
          >
            Identify this item →
          </button>
          {!imageFile && (
            <p
              style={{
                fontSize: 13,
                color: 'var(--color-text-tertiary)',
                textAlign: 'center',
                margin: '10px 0 0',
              }}
            >
              Add a photo above to classify the item.
            </p>
          )}
        </>
      )}
    </div>
  );
}
