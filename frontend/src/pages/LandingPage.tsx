import { Link } from 'react-router-dom';
import {
  Recycle,
  Camera,
  ArrowRight,
  Trash2,
  Hand,
  EyeOff,
  ScanLine,
  Database,
  Users,
  Building2,
  Landmark,
  BarChart3,
  AlertTriangle,
  CheckCircle,
  Layers,
  Truck,
} from 'lucide-react';
import { BinCard } from '../components/BinCard';
import { ConfidenceBar } from '../components/ConfidenceBar';
import { MaterialBadge } from '../components/MaterialBadge';

/* ── Small building blocks ──────────────────────────────── */

function SectionHeading({
  id,
  label,
  title,
  body,
}: {
  id: string;
  label: string;
  title: string;
  body?: string;
}) {
  return (
    <div style={{ maxWidth: 640, marginBottom: 'var(--space-10)' }}>
      <div className="section-label">{label}</div>
      <h2 id={id} className="landing-h2">{title}</h2>
      {body && (
        <p
          style={{
            fontSize: 17,
            lineHeight: 1.6,
            color: 'var(--color-text-secondary)',
            margin: 0,
          }}
        >
          {body}
        </p>
      )}
    </div>
  );
}

function StepCard({
  index,
  icon: Icon,
  title,
  body,
}: {
  index: number;
  icon: React.ComponentType<{ size?: number; style?: React.CSSProperties; 'aria-hidden'?: boolean }>;
  title: string;
  body: string;
}) {
  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
        <span className="landing-step-num" aria-hidden="true">{index}</span>
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 12,
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
            color: 'var(--color-text-tertiary)',
          }}
        >
          Step {index}
        </span>
      </div>
      <div className="landing-step-icon" aria-hidden="true">
        <Icon size={20} />
      </div>
      <div>
        <h3
          style={{
            fontSize: 18,
            fontWeight: 600,
            margin: '0 0 var(--space-2)',
            color: 'var(--color-text-primary)',
          }}
        >
          {title}
        </h3>
        <p
          style={{
            fontSize: 15,
            lineHeight: 1.6,
            color: 'var(--color-text-secondary)',
            margin: 0,
          }}
        >
          {body}
        </p>
      </div>
    </div>
  );
}

function FlowNode({
  icon: Icon,
  title,
  body,
}: {
  icon: React.ComponentType<{ size?: number; style?: React.CSSProperties; 'aria-hidden'?: boolean }>;
  title: string;
  body: string;
}) {
  return (
    <div className="landing-flow-node">
      <div style={{ color: 'var(--color-amber)' }} aria-hidden="true">
        <Icon size={22} />
      </div>
      <div>
        <h3
          style={{
            fontSize: 16,
            fontWeight: 600,
            margin: '0 0 var(--space-1)',
            color: 'var(--color-text-primary)',
          }}
        >
          {title}
        </h3>
        <p style={{ fontSize: 14, lineHeight: 1.55, color: 'var(--color-text-secondary)', margin: 0 }}>
          {body}
        </p>
      </div>
    </div>
  );
}

function MeasureCard({
  icon: Icon,
  title,
  body,
}: {
  icon: React.ComponentType<{ size?: number; style?: React.CSSProperties; 'aria-hidden'?: boolean }>;
  title: string;
  body: string;
}) {
  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      <div className="landing-step-icon" aria-hidden="true">
        <Icon size={20} />
      </div>
      <div>
        <h3
          style={{
            fontSize: 17,
            fontWeight: 600,
            margin: '0 0 var(--space-2)',
            color: 'var(--color-text-primary)',
          }}
        >
          {title}
        </h3>
        <p
          style={{
            fontSize: 14,
            lineHeight: 1.6,
            color: 'var(--color-text-secondary)',
            margin: 0,
          }}
        >
          {body}
        </p>
      </div>
      <div
        style={{
          marginTop: 'auto',
          display: 'inline-flex',
          alignItems: 'center',
          gap: 8,
          fontSize: 12,
          fontFamily: 'var(--font-mono)',
          color: 'var(--color-text-tertiary)',
        }}
      >
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: 'var(--color-border-strong)',
            flexShrink: 0,
          }}
          aria-hidden="true"
        />
        Ward dashboard
      </div>
    </div>
  );
}

function AudienceCard({
  icon: Icon,
  title,
  body,
  to,
  cta,
}: {
  icon: React.ComponentType<{ size?: number; style?: React.CSSProperties; 'aria-hidden'?: boolean }>;
  title: string;
  body: string;
  to: string;
  cta: string;
}) {
  return (
    <Link
      to={to}
      className="card card-interactive"
      style={{ textDecoration: 'none', display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}
    >
      <div className="landing-step-icon" aria-hidden="true">
        <Icon size={20} />
      </div>
      <div>
        <h3
          style={{
            fontSize: 18,
            fontWeight: 600,
            margin: '0 0 var(--space-2)',
            color: 'var(--color-text-primary)',
          }}
        >
          {title}
        </h3>
        <p
          style={{
            fontSize: 15,
            lineHeight: 1.6,
            color: 'var(--color-text-secondary)',
            margin: '0 0 var(--space-4)',
          }}
        >
          {body}
        </p>
        <span
          style={{
            fontSize: 14,
            fontWeight: 600,
            color: 'var(--color-amber)',
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          {cta} <ArrowRight size={15} aria-hidden="true" />
        </span>
      </div>
    </Link>
  );
}

/** Inline illustration of the photographed item — no external assets. */
function BottleIllustration() {
  return (
    <svg
      viewBox="0 0 120 160"
      width="112"
      height="149"
      role="img"
      aria-label="Illustration of a plastic bottle"
      style={{ display: 'block' }}
    >
      <rect x="49" y="6" width="22" height="13" rx="4" fill="var(--color-border-strong)" />
      <path
        d="M53 19 h14 v13 c0 6 11 9 11 24 v72 a12 12 0 0 1-12 12 H54 a12 12 0 0 1-12-12 V56 c0-15 11-18 11-24 Z"
        fill="rgba(240,234,214,0.08)"
        stroke="var(--color-text-secondary)"
        strokeWidth="2"
        strokeLinejoin="round"
      />
      <line x1="47" y1="82" x2="73" y2="82" stroke="var(--color-mat-plastic)" strokeWidth="2.5" opacity="0.75" />
      <line x1="47" y1="94" x2="73" y2="94" stroke="var(--color-mat-plastic)" strokeWidth="2.5" opacity="0.5" />
      <line x1="47" y1="106" x2="73" y2="106" stroke="var(--color-mat-plastic)" strokeWidth="2.5" opacity="0.3" />
    </svg>
  );
}

/* ── Page ───────────────────────────────────────────────── */

export default function LandingPage() {
  return (
    <div>
      {/* Header */}
      <header className="landing-header" role="banner">
        <Link
          to="/"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            textDecoration: 'none',
            color: 'var(--color-text-primary)',
            flexShrink: 0,
          }}
          aria-label="LoopWise home"
        >
          <Recycle size={24} style={{ color: 'var(--color-amber)' }} aria-hidden="true" />
          <span
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 20,
              fontWeight: 700,
            }}
          >
            LoopWise
          </span>
        </Link>

        <nav className="landing-nav-desktop" aria-label="Landing page sections">
          <a className="landing-nav-link" href="#how-it-works">
            How it works
          </a>
          <a className="landing-nav-link" href="#dashboard">
            For cities
          </a>
          <a className="landing-nav-link" href="#who-its-for">
            Who it's for
          </a>
        </nav>

        <div style={{ flex: 1 }} />

        <Link
          to="/analytics"
          className="btn btn-secondary landing-header-secondary"
          style={{ fontSize: 14, padding: '8px 16px', height: 40 }}
        >
          Open the dashboard
        </Link>
        <Link to="/classify" className="btn btn-primary" style={{ fontSize: 14, padding: '8px 16px', height: 40 }}>
          <Camera size={16} aria-hidden="true" />
          Identify an item
        </Link>
      </header>

      {/* Hero */}
      <section
        className="landing-section landing-hero-shell"
        style={{ paddingTop: 'var(--space-16)' }}
        aria-labelledby="hero-heading"
      >
        <div className="landing-container landing-grid-2">
          <div className="landing-fade-up">
            <div className="landing-eyebrow" style={{ marginBottom: 'var(--space-5)' }}>
              <ScanLine size={15} aria-hidden="true" />
              AI-powered waste segregation
            </div>
            <h1 id="hero-heading" className="landing-h1" style={{ marginBottom: 'var(--space-5)' }}>
              Every waste item has a{' '}
              <em
                style={{
                  color: 'var(--color-amber)',
                  fontStyle: 'italic',
                  fontWeight: 400,
                }}
              >
                next life
              </em>
              .
            </h1>
            <p
              style={{
                fontSize: 17,
                lineHeight: 1.6,
                color: 'var(--color-text-secondary)',
                margin: '0 0 var(--space-8)',
                maxWidth: 540,
              }}
            >
              LoopWise identifies a waste item's material from a single photo, recommends
              exactly how to sort it, and gives communities the ward-level picture of what
              keeps getting thrown away wrong.
            </p>
            <div style={{ display: 'flex', gap: 'var(--space-4)', flexWrap: 'wrap' }}>
              <Link to="/classify" className="btn btn-primary">
                <Camera size={18} aria-hidden="true" />
                Identify an item
              </Link>
              <Link to="/analytics" className="btn btn-secondary">
                <BarChart3 size={18} aria-hidden="true" />
                Explore the dashboard
              </Link>
            </div>
            <ul
              style={{
                listStyle: 'none',
                display: 'flex',
                flexWrap: 'wrap',
                gap: 'var(--space-3)',
                margin: 'var(--space-8) 0 0',
                padding: 0,
              }}
              aria-label="What LoopWise does"
            >
              <li className="landing-chip">
                <CheckCircle size={14} style={{ color: 'var(--color-signal-good)', flexShrink: 0 }} aria-hidden="true" />
                Real ONNX image classification
              </li>
              <li className="landing-chip">
                <Layers size={14} style={{ color: 'var(--color-amber)', flexShrink: 0 }} aria-hidden="true" />
                8 material categories
              </li>
              <li className="landing-chip">
                <Trash2 size={14} style={{ color: 'var(--color-bin-dry)', flexShrink: 0 }} aria-hidden="true" />
                Actionable disposal guidance
              </li>
            </ul>
          </div>

          {/* Product showcase — an illustrative result, built from real app components */}
          <div
            className="landing-showcase-shell landing-fade-up"
            style={{ animationDelay: '120ms' }}
            aria-label="Example classification result"
          >
            <div
              className="card landing-showcase"
              style={{ padding: 'var(--space-6)', boxShadow: 'var(--shadow-lg)' }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 'var(--space-3)',
                  marginBottom: 'var(--space-4)',
                }}
              >
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 600,
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase',
                    color: 'var(--color-text-tertiary)',
                  }}
                >
                  What a resident sees
                </span>
                <span
                  className="badge"
                  style={{ background: 'var(--color-amber-dim)', color: 'var(--color-amber)' }}
                >
                  Example
                </span>
              </div>

              {/* 1. The uploaded item */}
              <div className="landing-showcase-media">
                <span className="landing-scan" aria-hidden="true" />
                <BottleIllustration />
                <span
                  style={{
                    position: 'absolute',
                    bottom: 8,
                    left: 12,
                    fontSize: 11,
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--color-text-tertiary)',
                  }}
                >
                  photo of the item
                </span>
              </div>

              {/* 2. Predicted category — the primary answer */}
              <div className="section-label" style={{ marginBottom: 'var(--space-2)' }}>
                Waste category
              </div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--space-3)',
                  marginBottom: 'var(--space-4)',
                  flexWrap: 'wrap',
                }}
              >
                <span
                  className="font-display"
                  style={{ fontSize: 28, fontWeight: 600, color: 'var(--color-text-primary)', lineHeight: 1.15 }}
                >
                  Plastic
                </span>
                <MaterialBadge category="plastic" />
              </div>

              {/* 3. Model confidence */}
              <div style={{ marginBottom: 'var(--space-4)' }}>
                <ConfidenceBar confidence={0.87} confidenceLabel="Very sure" />
              </div>

              {/* 4. Recommended bin — secondary */}
              <div className="section-label" style={{ marginBottom: 'var(--space-2)' }}>
                Where it goes
              </div>
              <BinCard disposalBin="dry" action="Rinse it, then place it in this bin" compact />

              <p
                style={{
                  fontSize: 13,
                  lineHeight: 1.6,
                  color: 'var(--color-text-tertiary)',
                  margin: 'var(--space-4) 0 0',
                }}
              >
                Next life: recycled into polyester fibre or new bottles.
              </p>
            </div>
            <p
              style={{
                fontSize: 12,
                color: 'var(--color-text-tertiary)',
                textAlign: 'center',
                marginTop: 'var(--space-4)',
                paddingLeft: 'var(--space-6)',
                paddingRight: 'var(--space-6)',
              }}
            >
              Illustrative example — not a live prediction. Classifying your own item takes a
              photo and runs the live vision model.
            </p>
          </div>
        </div>
      </section>

      {/* Where the loop breaks */}
      <section
        className="landing-section"
        style={{ background: 'var(--color-surface-1)', borderTop: '1px solid var(--color-border)', borderBottom: '1px solid var(--color-border)' }}
        aria-labelledby="problem-heading"
      >
        <div className="landing-container">
          <SectionHeading
            id="problem-heading"
            label="The problem"
            title="Where the loop breaks"
            body="A circular system depends on clean, sorted material reaching recoverers. It fails long before the truck."
          />
          <div className="landing-grid-4">
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div className="landing-step-icon" style={{ background: 'var(--color-signal-bad-dim)', borderColor: 'transparent' }} aria-hidden="true">
                  <Trash2 size={18} style={{ color: 'var(--color-signal-bad)' }} />
                </div>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--color-text-tertiary)' }} aria-hidden="true">
                  01
                </span>
              </div>
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 600, margin: '0 0 var(--space-2)', color: 'var(--color-text-primary)' }}>
                  Mixed at the doorstep
                </h3>
                <p style={{ fontSize: 14, lineHeight: 1.6, color: 'var(--color-text-secondary)', margin: 0 }}>
                  Wet and dry waste go in together before the truck ever arrives. Segregation
                  mandates fail here first.
                </p>
              </div>
            </div>
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div className="landing-step-icon" aria-hidden="true">
                  <AlertTriangle size={18} style={{ color: 'var(--color-signal-warn)' }} />
                </div>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--color-text-tertiary)' }} aria-hidden="true">
                  02
                </span>
              </div>
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 600, margin: '0 0 var(--space-2)', color: 'var(--color-text-primary)' }}>
                  Recyclables get contaminated
                </h3>
                <p style={{ fontSize: 14, lineHeight: 1.6, color: 'var(--color-text-secondary)', margin: 0 }}>
                  A bottle with food residue has no buyer. Contaminated material goes to landfill
                  with everything else.
                </p>
              </div>
            </div>
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div className="landing-step-icon" style={{ background: 'var(--color-signal-bad-dim)', borderColor: 'transparent' }} aria-hidden="true">
                  <Hand size={18} style={{ color: 'var(--color-signal-bad)' }} />
                </div>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--color-text-tertiary)' }} aria-hidden="true">
                  03
                </span>
              </div>
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 600, margin: '0 0 var(--space-2)', color: 'var(--color-text-primary)' }}>
                  Sorted by hand at a cost
                </h3>
                <p style={{ fontSize: 14, lineHeight: 1.6, color: 'var(--color-text-secondary)', margin: 0 }}>
                  Informal workers pick through mixed waste to recover what still can be — at
                  their own health risk.
                </p>
              </div>
            </div>
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div className="landing-step-icon" aria-hidden="true">
                  <EyeOff size={18} style={{ color: 'var(--color-text-tertiary)' }} />
                </div>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--color-text-tertiary)' }} aria-hidden="true">
                  04
                </span>
              </div>
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 600, margin: '0 0 var(--space-2)', color: 'var(--color-text-primary)' }}>
                  Cities can't see it
                </h3>
                <p style={{ fontSize: 14, lineHeight: 1.6, color: 'var(--color-text-secondary)', margin: 0 }}>
                  There is no data on which items are misjudged, where, and when. You can't fix
                  what you can't measure.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="landing-section" aria-labelledby="how-heading">
        <div className="landing-container">
          <SectionHeading
            id="how-heading"
            label="How it works"
            title="Upload. Identify. Sort correctly."
            body="One photo from a resident becomes an answer at the bin — and ground truth for an entire ward."
          />
          <div className="landing-grid-3 landing-steps-grid">
            <StepCard
              index={1}
              icon={Camera}
              title="Upload a photo"
              body="Open the classifier on a phone and photograph whatever you're about to throw out."
            />
            <StepCard
              index={2}
              icon={ScanLine}
              title="Identify the material"
              body="The live ONNX vision model names one of eight material categories and how confident it is."
            />
            <StepCard
              index={3}
              icon={Trash2}
              title="Sort it correctly"
              body="See the right bin, the item's next life, and simple do / don't tips — then toss it with confidence."
            />
          </div>
          <div
            className="data-honesty-footer"
            style={{ marginTop: 'var(--space-8)' }}
            role="note"
          >
            <Database size={16} style={{ color: 'var(--color-amber)', flexShrink: 0, marginTop: 2 }} aria-hidden="true" />
            <span>
              Every confirmation and correction is logged, so the system learns from its own
              mistakes — a wrong guess fixed by a resident becomes training signal for the next
              one.
            </span>
          </div>
        </div>
      </section>

      {/* The loop + for cities */}
      <section
        id="dashboard"
        className="landing-section"
        style={{ background: 'var(--color-surface-1)', borderTop: '1px solid var(--color-border)', borderBottom: '1px solid var(--color-border)' }}
        aria-labelledby="dashboard-heading"
      >
        <div className="landing-container">
          <SectionHeading
            id="dashboard-heading"
            label="From a sorted item to a recovered material"
            title="Correct sorting is what makes recovery possible"
            body="Every item a resident sorts correctly reaches a recoverer as clean, usable material instead of landfill-bound contamination."
          />

          <div className="landing-flow" style={{ marginBottom: 'var(--space-12)' }}>
            <FlowNode
              icon={Camera}
              title="Photograph the item"
              body="A resident points a phone at what they're about to discard."
            />
            <span className="landing-flow-arrow" aria-hidden="true">
              <ArrowRight size={20} />
            </span>
            <FlowNode
              icon={Trash2}
              title="Sort at the source"
              body="The right bin, before wet and dry waste mix at the doorstep."
            />
            <span className="landing-flow-arrow" aria-hidden="true">
              <ArrowRight size={20} />
            </span>
            <FlowNode
              icon={Truck}
              title="Clean stream to recoverers"
              body="Uncontaminated material a kabadiwala, compostor, or plant can actually use."
            />
            <span className="landing-flow-arrow" aria-hidden="true">
              <ArrowRight size={20} />
            </span>
            <FlowNode
              icon={Recycle}
              title="Back in the loop"
              body="Compost, pulp, or flake — the item's next life begins with one correct toss."
            />
          </div>

          <div style={{ maxWidth: 640, marginBottom: 'var(--space-8)' }}>
            <div className="section-label">For municipalities and housing societies</div>
            <h3
              className="font-display"
              style={{ fontSize: 22, fontWeight: 600, color: 'var(--color-text-primary)', margin: '0 0 var(--space-2)' }}
            >
              What the ward dashboard shows
            </h3>
            <p style={{ fontSize: 15, lineHeight: 1.6, color: 'var(--color-text-secondary)', margin: 0 }}>
              Resident classifications roll up into ward-level measures — no jargon, no
              unverified claims, just what was actually sorted.
            </p>
          </div>

          <div className="landing-grid-3">
            <MeasureCard
              icon={AlertTriangle}
              title="Ward contamination"
              body="See what share of sorted items is wrongly binned, ward by ward, from real resident classifications."
            />
            <MeasureCard
              icon={Recycle}
              title="Recovery potential"
              body="Understand how much dry and organic material could re-enter the loop if it were sorted correctly at source."
            />
            <MeasureCard
              icon={BarChart3}
              title="What keeps going wrong"
              body="Top misclassifications show which items confuse residents — evidence for a signboard, a workshop, or a producer conversation."
            />
          </div>

          <div
            className="data-honesty-footer"
            style={{ marginTop: 'var(--space-8)' }}
            role="note"
          >
            <Database size={16} style={{ color: 'var(--color-amber)', flexShrink: 0, marginTop: 2 }} aria-hidden="true" />
            <span>
              Every classification and correction is logged, building the first ground-truth
              dataset of what urban India throws away — and what it gets wrong. Dashboard
              figures describe items sorted through LoopWise, not an entire ward's waste stream.
            </span>
          </div>

          <div style={{ marginTop: 'var(--space-8)', display: 'flex', gap: 'var(--space-4)', flexWrap: 'wrap' }}>
            <Link to="/analytics" className="btn btn-primary">
              Open the dashboard
              <ArrowRight size={18} aria-hidden="true" />
            </Link>
            <Link to="/analytics/ward/WD-DEMO-A" className="btn btn-secondary">
              See a demo ward
            </Link>
          </div>
        </div>
      </section>

      {/* Who it's for */}
      <section id="who-its-for" className="landing-section" aria-labelledby="audience-heading">
        <div className="landing-container">
          <SectionHeading id="audience-heading" label="Who it's for" title="Built for everyone downstream of the bin" />
          <div className="landing-grid-3">
            <AudienceCard
              icon={Users}
              title="Residents"
              body="Identify an item before you throw it out. Get the bin, the next life, and who recovers it — in plain language."
              to="/classify"
              cta="Identify an item"
            />
            <AudienceCard
              icon={Building2}
              title="Housing societies"
              body="See how well your building sorts, which items keep getting it wrong, and where a simple signboard would help."
              to="/analytics"
              cta="Open the dashboard"
            />
            <AudienceCard
              icon={Landmark}
              title="Municipalities"
              body="Compare wards, find contamination hotspots, and take design-for-recycling gaps to producers with evidence."
              to="/analytics"
              cta="Compare wards"
            />
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section
        className="landing-section landing-hero-shell"
        style={{ background: 'var(--color-surface-1)', borderTop: '1px solid var(--color-border)' }}
        aria-labelledby="cta-heading"
      >
        <div className="landing-container" style={{ textAlign: 'center', maxWidth: 720, position: 'relative' }}>
          <div className="landing-eyebrow" style={{ justifyContent: 'center', marginBottom: 'var(--space-4)' }}>
            <ScanLine size={15} aria-hidden="true" />
            Try it now
          </div>
          <h2 id="cta-heading" className="landing-h2">
            Try it on the next item you throw out.
          </h2>
          <p
            style={{
              fontSize: 17,
              lineHeight: 1.6,
              color: 'var(--color-text-secondary)',
              margin: '0 0 var(--space-8)',
            }}
          >
            No sign-up needed. Take a photo — LoopWise will tell you where it goes.
          </p>
          <div
            style={{
              display: 'flex',
              gap: 'var(--space-4)',
              justifyContent: 'center',
              flexWrap: 'wrap',
            }}
          >
            <Link to="/classify" className="btn btn-primary">
              <Camera size={18} aria-hidden="true" />
              Identify an item
            </Link>
            <Link to="/analytics" className="btn btn-secondary">
              Open the dashboard
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer
        className="landing-footer"
        style={{ borderTop: '1px solid var(--color-border)' }}
        role="contentinfo"
      >
        <div className="landing-container">
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 'var(--space-8)',
              justifyContent: 'space-between',
              marginBottom: 'var(--space-8)',
            }}
          >
            <div style={{ maxWidth: 320 }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  marginBottom: 'var(--space-3)',
                }}
              >
                <Recycle size={20} style={{ color: 'var(--color-amber)' }} aria-hidden="true" />
                <span style={{ fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 700 }}>
                  LoopWise
                </span>
              </div>
              <p style={{ fontSize: 14, lineHeight: 1.6, color: 'var(--color-text-secondary)', margin: 0 }}>
                A segregation-intelligence layer that keeps material in the loop — from the
                doorstep bin to the ward dashboard.
              </p>
            </div>
            <nav aria-label="Footer" style={{ display: 'flex', gap: 'var(--space-12)', flexWrap: 'wrap' }}>
              <div>
                <div className="section-label" style={{ marginBottom: 'var(--space-3)' }}>
                  Use LoopWise
                </div>
                <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'grid', gap: 'var(--space-2)' }}>
                  <li>
                    <Link className="landing-nav-link" to="/classify" style={{ padding: 0 }}>
                      Identify an item
                    </Link>
                  </li>
                  <li>
                    <Link className="landing-nav-link" to="/analytics" style={{ padding: 0 }}>
                      Dashboard
                    </Link>
                  </li>
                  <li>
                    <Link className="landing-nav-link" to="/analytics/ward/WD-DEMO-A" style={{ padding: 0 }}>
                      Demo ward
                    </Link>
                  </li>
                </ul>
              </div>
              <div>
                <div className="section-label" style={{ marginBottom: 'var(--space-3)' }}>
                  Learn
                </div>
                <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'grid', gap: 'var(--space-2)' }}>
                  <li>
                    <Link className="landing-nav-link" to="/materials" style={{ padding: 0 }}>
                      Materials guide
                    </Link>
                  </li>
                  <li>
                    <Link className="landing-nav-link" to="/help" style={{ padding: 0 }}>
                      Help &amp; tour
                    </Link>
                  </li>
                </ul>
              </div>
            </nav>
          </div>

        </div>
      </footer>
    </div>
  );
}
