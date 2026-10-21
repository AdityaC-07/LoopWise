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
  RefreshCw,
  Users,
  Building2,
  Landmark,
  BarChart3,
  AlertTriangle,
  Check,
  X,
} from 'lucide-react';
import { BinCard } from '../components/BinCard';
import { ConfidenceBar } from '../components/ConfidenceBar';
import { RecoveryBar } from '../components/RecoveryBar';
import { MaterialBadge } from '../components/MaterialBadge';
import { StatusLight } from '../components/StatusLight';

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

function MiniBar({
  width,
  color,
  label,
}: {
  width: string;
  color: string;
  label: string;
}) {
  return (
    <div
      className="mini-bar-track"
      role="img"
      aria-label={`${label} (illustrative)`}
      style={{ marginTop: 'var(--space-4)' }}
    >
      <div className="mini-bar-fill" style={{ width, background: color }} aria-hidden="true" />
    </div>
  );
}

function MetricCard({
  title,
  body,
  barWidth,
  barColor,
  barLabel,
  children,
}: {
  title: string;
  body: string;
  barWidth: string;
  barColor: string;
  barLabel: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
      <div
        style={{
          fontSize: 11,
          fontWeight: 600,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          color: 'var(--color-text-tertiary)',
          marginBottom: 'var(--space-2)',
        }}
      >
        Ward measure
      </div>
      <h3
        style={{
          fontFamily: 'var(--font-display)',
          fontSize: 20,
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
          flex: 1,
        }}
      >
        {body}
      </p>
      <MiniBar width={barWidth} color={barColor} label={barLabel} />
      {children}
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
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: 'var(--radius-md)',
            background: 'var(--color-amber-dim)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
          aria-hidden="true"
        >
          <Icon size={20} style={{ color: 'var(--color-amber)' }} />
        </div>
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 13,
            color: 'var(--color-text-tertiary)',
          }}
        >
          Step {index}
        </span>
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
      <div
        style={{
          width: 44,
          height: 44,
          borderRadius: 'var(--radius-md)',
          background: 'var(--color-surface-2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
        aria-hidden="true"
      >
        <Icon size={22} style={{ color: 'var(--color-amber)' }} />
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
      <section className="landing-section" style={{ paddingTop: 'var(--space-16)' }} aria-labelledby="hero-heading">
        <div className="landing-container landing-grid-2">
          <div>
            <div
              className="badge"
              style={{
                background: 'var(--color-amber-dim)',
                color: 'var(--color-amber)',
                marginBottom: 'var(--space-5)',
              }}
            >
              Segregation intelligence for urban India
            </div>
            <h1 id="hero-heading" className="landing-h1" style={{ marginBottom: 'var(--space-5)' }}>
              The loop breaks at the bin. LoopWise keeps material in it.
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
              When wet and dry waste are mixed at the doorstep, recyclable material is
              contaminated and lands in landfill. LoopWise tells a resident exactly where each
              item goes — and gives cities the data to fix what keeps going wrong.
            </p>
            <div style={{ display: 'flex', gap: 'var(--space-4)', flexWrap: 'wrap' }}>
              <Link to="/classify" className="btn btn-primary">
                <Camera size={18} aria-hidden="true" />
                Identify an item
              </Link>
              <Link to="/analytics" className="btn btn-secondary">
                <BarChart3 size={18} aria-hidden="true" />
                Open the dashboard
              </Link>
            </div>
            <p
              style={{
                fontSize: 13,
                color: 'var(--color-text-tertiary)',
                marginTop: 'var(--space-6)',
                lineHeight: 1.6,
              }}
            >
              Runs on a phone or a fixed overhead camera at a community bin. Identifies an item
              in under a second.
            </p>
          </div>

          {/* Product visual — example classification result, built from real app components */}
          <div aria-label="Example classification result">
            <div
              className="card"
              style={{ padding: 'var(--space-6)', boxShadow: 'var(--shadow-lg)' }}
            >
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  color: 'var(--color-text-tertiary)',
                  marginBottom: 'var(--space-4)',
                }}
              >
                Example — what a resident sees
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
                  style={{ fontSize: 26, fontWeight: 600, color: 'var(--color-text-primary)' }}
                >
                  PET Plastic Bottle
                </span>
                <MaterialBadge category="plastic" />
              </div>

              <BinCard disposalBin="dry" action="Rinse it, then place it in this bin" />

              <div style={{ marginTop: 'var(--space-5)' }}>
                <ConfidenceBar confidence={0.87} confidenceLabel="Very sure" />
              </div>
              <div style={{ marginTop: 'var(--space-4)' }}>
                <RecoveryBar recoveryPotential="high" />
              </div>

              <hr className="divider" style={{ margin: 'var(--space-5) 0' }} />

              <div style={{ fontSize: 15, color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
                <span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>
                  What happens next:
                </span>{' '}
                Recycled into polyester fibre or new bottles. Collected by your local kabadiwala.
              </div>

              <ul
                style={{
                  listStyle: 'none',
                  margin: 'var(--space-4) 0 0',
                  padding: 0,
                  display: 'grid',
                  gap: 6,
                  fontSize: 14,
                  color: 'var(--color-text-secondary)',
                }}
              >
                <li style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                  <Check size={16} style={{ color: 'var(--color-signal-good)', flexShrink: 0, marginTop: 2 }} aria-hidden="true" />
                  Remove the cap, then crush it
                </li>
                <li style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                  <X size={16} style={{ color: 'var(--color-signal-bad)', flexShrink: 0, marginTop: 2 }} aria-hidden="true" />
                  Do not leave food or liquid inside
                </li>
              </ul>
            </div>
            <p
              style={{
                fontSize: 12,
                color: 'var(--color-text-tertiary)',
                textAlign: 'center',
                marginTop: 'var(--space-3)',
              }}
            >
              Example result shown for illustration. Your classification comes from the live
              vision model.
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
            <div className="card">
              <Trash2 size={22} style={{ color: 'var(--color-signal-bad)', marginBottom: 'var(--space-4)' }} aria-hidden="true" />
              <h3 style={{ fontSize: 16, fontWeight: 600, margin: '0 0 var(--space-2)', color: 'var(--color-text-primary)' }}>
                Mixed at the doorstep
              </h3>
              <p style={{ fontSize: 14, lineHeight: 1.6, color: 'var(--color-text-secondary)', margin: 0 }}>
                Wet and dry waste go in together before the truck ever arrives. Segregation
                mandates fail here first.
              </p>
            </div>
            <div className="card">
              <AlertTriangle size={22} style={{ color: 'var(--color-signal-warn)', marginBottom: 'var(--space-4)' }} aria-hidden="true" />
              <h3 style={{ fontSize: 16, fontWeight: 600, margin: '0 0 var(--space-2)', color: 'var(--color-text-primary)' }}>
                Recyclables get contaminated
              </h3>
              <p style={{ fontSize: 14, lineHeight: 1.6, color: 'var(--color-text-secondary)', margin: 0 }}>
                A bottle with food residue has no buyer. Contaminated material goes to landfill
                with everything else.
              </p>
            </div>
            <div className="card">
              <Hand size={22} style={{ color: 'var(--color-signal-bad)', marginBottom: 'var(--space-4)' }} aria-hidden="true" />
              <h3 style={{ fontSize: 16, fontWeight: 600, margin: '0 0 var(--space-2)', color: 'var(--color-text-primary)' }}>
                Sorted by hand at a cost
              </h3>
              <p style={{ fontSize: 14, lineHeight: 1.6, color: 'var(--color-text-secondary)', margin: 0 }}>
                Informal workers pick through mixed waste to recover what still can be — at
                their own health risk.
              </p>
            </div>
            <div className="card">
              <EyeOff size={22} style={{ color: 'var(--color-text-tertiary)', marginBottom: 'var(--space-4)' }} aria-hidden="true" />
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
      </section>

      {/* How it works */}
      <section id="how-it-works" className="landing-section" aria-labelledby="how-heading">
        <div className="landing-container">
          <SectionHeading
            id="how-heading"
            label="How it works"
            title="Point. Sort. Close the loop."
            body="One action from a resident becomes ground truth for an entire ward."
          />
          <div className="landing-grid-3">
            <StepCard
              index={1}
              icon={ScanLine}
              title="Point at an item"
              body="A resident points a phone — or a fixed overhead camera at a community bin — at whatever they're about to throw out."
            />
            <StepCard
              index={2}
              icon={Recycle}
              title="See where it goes"
              body="LoopWise names the correct bin, the item's next life — reuse, recycle, compost, or non-recoverable — and who recovers it, such as a local kabadiwala or processor."
            />
            <StepCard
              index={3}
              icon={RefreshCw}
              title="Corrections make it smarter"
              body="Every classification, and every correction of a wrong guess, is logged. The model retrains on its own mistakes."
            />
          </div>
        </div>
      </section>

      {/* Dashboard / for cities */}
      <section
        id="dashboard"
        className="landing-section"
        style={{ background: 'var(--color-surface-1)', borderTop: '1px solid var(--color-border)', borderBottom: '1px solid var(--color-border)' }}
        aria-labelledby="dashboard-heading"
      >
        <div className="landing-container">
          <SectionHeading
            id="dashboard-heading"
            label="For municipalities and housing societies"
            title="Three numbers a city can act on"
            body="The dashboard turns resident classifications into ward-level circularity measures — no jargon, no unverified claims, just what was actually sorted."
          />
          <div className="landing-grid-3">
            <MetricCard
              title="Wrongly sorted"
              body="How much recoverable material is lost to mixing. High rates pinpoint wards and items where segregation is failing."
              barWidth="18%"
              barColor="var(--color-signal-bad)"
              barLabel="18 percent wrongly sorted (example)"
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginTop: 'var(--space-4)' }}>
                <StatusLight contaminationRate={0.18} showLabel={false} />
                <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>18% — needs attention (example)</span>
              </div>
            </MetricCard>
            <MetricCard
              title="Recovery potential per ward"
              body="How much dry and organic waste could re-enter the loop if it were sorted correctly at the source."
              barWidth="74%"
              barColor="var(--color-signal-good)"
              barLabel="74 percent recovery potential (example)"
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginTop: 'var(--space-4)' }}>
                <StatusLight contaminationRate={0.05} showLabel={false} />
                <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>High potential (example)</span>
              </div>
            </MetricCard>
            <MetricCard
              title="Design-for-recycling gaps"
              body="Which packaging formats cannot be recycled at all — evidence your city can take to producers under extended responsibility rules."
              barWidth="31%"
              barColor="var(--color-signal-warn)"
              barLabel="31 percent non-recoverable formats (example)"
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginTop: 'var(--space-4)' }}>
                <StatusLight contaminationRate={0.31} showLabel={false} />
                <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>Mixed-material packs (example)</span>
              </div>
            </MetricCard>
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
        className="landing-section"
        style={{ background: 'var(--color-surface-1)', borderTop: '1px solid var(--color-border)' }}
        aria-labelledby="cta-heading"
      >
        <div className="landing-container" style={{ textAlign: 'center', maxWidth: 720 }}>
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
            No sign-up needed. Take a photo or describe the item — LoopWise will tell you where
            it goes.
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
