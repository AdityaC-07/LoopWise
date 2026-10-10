import { useEffect, useRef, useState } from 'react';

const TOUR_KEY = 'loopwise_tour_complete';

const TOUR_STEPS = [
  {
    targetSelector: null,
    heading: 'Welcome to LoopWise',
    body: "LoopWise helps you sort waste correctly and track how your ward is doing. We'll walk you through how it works. It only takes a minute.",
    position: 'center' as const,
  },
  {
    targetSelector: '#classify-upload-btn',
    heading: 'Take a photo to identify waste',
    body: 'Point your camera at an item or upload a photo. LoopWise will tell you exactly which bin it belongs in.',
    position: 'below' as const,
  },
  {
    targetSelector: '#classify-description',
    heading: 'Or describe it in words',
    body: "If you don't have a photo, just type what the item is — like \"plastic water bottle\" or \"old newspaper.\"",
    position: 'below' as const,
  },
  {
    targetSelector: '#result-bin-card',
    heading: 'See where it goes',
    body: 'LoopWise will show you the correct bin with clear instructions. The colour shows you exactly where it belongs.',
    position: 'below' as const,
  },
  {
    targetSelector: '#result-confidence-bar',
    heading: 'Check how sure we are',
    body: 'The bar shows how confident LoopWise is. If it says "Not very sure," you\'ll see other options to choose from.',
    position: 'below' as const,
  },
  {
    targetSelector: '#result-feedback-btn',
    heading: 'Tell us if we got it wrong',
    body: 'If the answer doesn\'t look right, tap here to correct it. This helps the system get better for everyone.',
    position: 'above' as const,
  },
  {
    targetSelector: '#analytics-overview',
    heading: 'See how your ward is doing',
    body: 'The Overview tab shows how waste sorting is going across your area — which items are often sorted incorrectly.',
    position: 'below' as const,
  },
  {
    targetSelector: '#nav-help',
    heading: 'Replay this tour any time',
    body: "If you ever need a reminder of how things work, tap the Help tab to replay this tour. You're all set!",
    position: 'above' as const,
  },
];

interface TourProps {
  onClose: () => void;
}

export function Tour({ onClose }: TourProps) {
  const [step, setStep] = useState(0);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);

  const current = TOUR_STEPS[step];

  useEffect(() => {
    if (current.targetSelector) {
      const el = document.querySelector(current.targetSelector);
      if (el) {
        setTargetRect(el.getBoundingClientRect());
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else {
        setTargetRect(null);
      }
    } else {
      setTargetRect(null);
    }
  }, [step, current.targetSelector]);

  // Handle keyboard
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') handleSkip();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  });

  // Focus trap inside tooltip
  useEffect(() => {
    tooltipRef.current?.focus();
  }, [step]);

  function handleNext() {
    if (step < TOUR_STEPS.length - 1) {
      setStep((s) => s + 1);
    } else {
      localStorage.setItem(TOUR_KEY, 'true');
      onClose();
    }
  }

  function handleSkip() {
    localStorage.setItem(TOUR_KEY, 'true');
    onClose();
  }

  function getTooltipPosition(): React.CSSProperties {
    if (!targetRect || current.position === 'center') {
      return {
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
      };
    }

    const margin = 16;
    const vw = window.innerWidth;

    // Default: below the target
    let top = targetRect.bottom + margin;
    let left = Math.min(
      Math.max(targetRect.left, margin),
      vw - 340
    );

    if (current.position === 'above' || targetRect.bottom + 260 > window.innerHeight) {
      top = targetRect.top - 260 - margin;
    }

    // Ensure within viewport
    top = Math.max(margin, Math.min(top, window.innerHeight - 280));
    return { top, left };
  }

  return (
    <>
      {/* Overlay */}
      <div className="tour-overlay" aria-hidden="true" />

      {/* Spotlight highlight for target element */}
      {targetRect && (
        <div
          style={{
            position: 'fixed',
            top: targetRect.top - 4,
            left: targetRect.left - 4,
            width: targetRect.width + 8,
            height: targetRect.height + 8,
            border: '2px solid var(--color-amber)',
            borderRadius: 'var(--radius-md)',
            zIndex: 1001,
            pointerEvents: 'none',
            transition: 'all 250ms ease-in-out',
          }}
          aria-hidden="true"
        />
      )}

      {/* Tooltip */}
      <div
        ref={tooltipRef}
        className="tour-tooltip"
        role="dialog"
        aria-modal="true"
        aria-label={`Tour step ${step + 1} of ${TOUR_STEPS.length}: ${current.heading}`}
        tabIndex={-1}
        style={getTooltipPosition()}
      >
        <div
          aria-live="polite"
          style={{ marginBottom: 16 }}
        >
          <div
            style={{
              fontSize: '13px',
              fontWeight: 500,
              color: 'var(--color-text-secondary)',
              marginBottom: 8,
            }}
          >
            Step {step + 1} of {TOUR_STEPS.length}
          </div>
          <h2
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: 18,
              fontWeight: 600,
              color: 'var(--color-text-primary)',
              margin: '0 0 8px',
            }}
          >
            {current.heading}
          </h2>
          <p
            style={{
              fontSize: '15px',
              color: 'var(--color-text-secondary)',
              margin: 0,
              lineHeight: 1.5,
            }}
          >
            {current.body}
          </p>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <button
            className="btn btn-ghost"
            onClick={handleSkip}
            style={{ color: 'var(--color-text-tertiary)', minWidth: 'unset', fontSize: '13px' }}
          >
            Skip tour
          </button>
          <button className="btn btn-primary" onClick={handleNext} style={{ minWidth: 100 }}>
            {step === TOUR_STEPS.length - 1 ? 'Got it ✓' : 'Next →'}
          </button>
        </div>
      </div>
    </>
  );
}

export function useTour() {
  const [showTour, setShowTour] = useState(false);

  useEffect(() => {
    const done = localStorage.getItem(TOUR_KEY);
    if (!done || done !== 'true') {
      const timer = setTimeout(() => setShowTour(true), 500);
      return () => clearTimeout(timer);
    }
  }, []);

  function startTour() {
    setShowTour(true);
  }

  function closeTour() {
    setShowTour(false);
  }

  return { showTour, startTour, closeTour };
}
