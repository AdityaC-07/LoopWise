import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import { getAnalyticsOverview } from '../api/client';
import { LoadingDots, ChartSkeleton } from '../components/Loading';
import { ErrorMessage } from '../components/ErrorMessage';
import { StatusLight } from '../components/StatusLight';
import { formatNumber, formatPercent } from '../utils/display';
import type { OverviewAnalytics } from '../types/api';

const MAT_COLORS: Record<string, string> = {
  plastic: '#8A9BB5',
  paper: '#C4903A',
  organic: '#7CA870',
  glass: '#4A9B8E',
  metal: '#9B9B8A',
  other: '#6E8A72',
  ewaste: '#9B7EC8',
  hazardous: '#C47A4A',
  composite: '#7A8B6E',
};

const DEMO_WARDS = [
  { id: 'WD-DEMO-A', name: 'Ward A', contamination: 0.08, events: 312 },
  { id: 'WD-DEMO-B', name: 'Ward B', contamination: 0.22, events: 198 },
  { id: 'WD-DEMO-C', name: 'Ward C', contamination: 0.05, events: 411 },
];

export default function AnalyticsOverviewPage() {
  const navigate = useNavigate();
  const [data, setData] = useState<OverviewAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAllMisc, setShowAllMisc] = useState(false);

  useEffect(() => {
    setLoading(true);
    getAnalyticsOverview()
      .then((r) => setData(r.data))
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="content-area"><LoadingDots label="Loading overview…" /></div>;

  const matBreakdownData = data
    ? Object.entries(data.material_breakdown).map(([name, value]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        value: Math.round(value * 100),
        color: MAT_COLORS[name] ?? '#6E8A72',
      }))
    : [];

  const visibleMisc = showAllMisc
    ? (data?.top_misclassifications ?? []).slice(0, 10)
    : (data?.top_misclassifications ?? []).slice(0, 5);

  return (
    <div className="content-area" id="analytics-overview">
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 28,
            fontWeight: 600,
            color: 'var(--color-text-primary)',
            margin: 0,
          }}
        >
          Overview
        </h1>
        {data?.demo_data && (
          <span
            style={{
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
            Demo data
          </span>
        )}
      </div>
      <p style={{ color: 'var(--color-text-secondary)', fontSize: 15, margin: '0 0 32px' }}>
        How waste sorting is going across all areas using this app.
      </p>

      {error && (
        <div style={{ marginBottom: 24 }}>
          <ErrorMessage message={error} onRetry={() => window.location.reload()} />
        </div>
      )}

      {/* Summary cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 'var(--card-gap)',
          marginBottom: 32,
        }}
      >
        <SummaryCard
          label="Items sorted"
          value={data ? formatNumber(data.summary.total_events) : '—'}
          sub="Total items classified this period"
        />
        <SummaryCard
          label="Wrongly sorted"
          value={data ? formatPercent(data.summary.contamination_rate) : '—'}
          sub="Items put in the wrong bin"
          signal={
            data
              ? data.summary.contamination_rate > 0.2
                ? 'bad'
                : data.summary.contamination_rate > 0.1
                ? 'warn'
                : 'good'
              : undefined
          }
        />
        <SummaryCard
          label="Recycling opportunity"
          value={data ? formatPercent(data.summary.recovery_potential_avg) : '—'}
          sub="How recyclable the sorted items are"
          signal="good"
        />
        <SummaryCard
          label="Uncertain answers"
          value={data ? formatPercent(data.summary.low_confidence_rate) : '—'}
          sub="Items we weren't confident about"
        />
      </div>

      {/* Ward status table */}
      <div style={{ marginBottom: 32 }}>
        <div className="section-label">Ward status</div>
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Ward</th>
                <th>Status</th>
                <th>Wrongly sorted</th>
                <th>Items sorted</th>
              </tr>
            </thead>
            <tbody>
              {DEMO_WARDS.map((ward) => (
                <tr
                  key={ward.id}
                  onClick={() => navigate(`/analytics/ward/${ward.id}`)}
                  style={{ cursor: 'pointer' }}
                  tabIndex={0}
                  onKeyDown={(e) => e.key === 'Enter' && navigate(`/analytics/ward/${ward.id}`)}
                  aria-label={`View analytics for ${ward.name}`}
                >
                  <td style={{ fontWeight: 500 }}>{ward.name}</td>
                  <td><StatusLight contaminationRate={ward.contamination} /></td>
                  <td className="tabular-nums">{formatPercent(ward.contamination)}</td>
                  <td className="tabular-nums">{formatNumber(ward.events)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p style={{ fontSize: 13, color: 'var(--color-text-tertiary)', marginTop: 8 }}>
          Click a row to view detailed analytics for that ward.
        </p>
      </div>

      {/* Material breakdown chart */}
      <div style={{ marginBottom: 32 }}>
        <div className="section-label">What's being sorted</div>
        <div className="card">
          {matBreakdownData.length === 0 ? (
            <ChartSkeleton />
          ) : (
            <>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart
                  data={matBreakdownData}
                  layout="vertical"
                  margin={{ top: 0, right: 16, bottom: 0, left: 16 }}
                >
                  <title>Material breakdown — proportion of each type</title>
                  <XAxis type="number" unit="%" tick={{ fill: 'var(--color-text-tertiary)', fontSize: 12 }} />
                  <YAxis type="category" dataKey="name" width={72} tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{
                      background: 'var(--color-surface-1)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--radius-md)',
                      color: 'var(--color-text-primary)',
                      fontSize: 13,
                    }}
                    formatter={(val: unknown) => [`${val as number}%`, 'Proportion']}
                  />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                    {matBreakdownData.map((entry, idx) => (
                      <Cell key={idx} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '10px 20px',
                  marginTop: 16,
                  paddingTop: 12,
                  borderTop: '1px solid var(--color-border)',
                }}
              >
                {matBreakdownData.map((entry) => (
                  <span
                    key={entry.name}
                    style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--color-text-secondary)' }}
                  >
                    <span
                      style={{ width: 10, height: 10, borderRadius: 2, background: entry.color, display: 'inline-block' }}
                      aria-hidden="true"
                    />
                    {entry.name}
                  </span>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Commonly confused items */}
      {(data?.top_misclassifications?.length ?? 0) > 0 && (
        <div style={{ marginBottom: 24 }}>
          <div className="section-label">Commonly confused items</div>
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Item we guessed</th>
                  <th style={{ textAlign: 'center' }}>→</th>
                  <th>Item it actually was</th>
                  <th style={{ textAlign: 'right' }}>Times reported</th>
                </tr>
              </thead>
              <tbody>
                {visibleMisc.map((item, idx) => (
                  <tr key={idx}>
                    <td>{item.predicted.replace(/_/g, ' ')}</td>
                    <td style={{ textAlign: 'center', color: 'var(--color-text-tertiary)' }}>→</td>
                    <td>{item.corrected.replace(/_/g, ' ')}</td>
                    <td style={{ textAlign: 'right' }} className="tabular-nums">{item.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {(data?.top_misclassifications?.length ?? 0) > 5 && (
            <button
              className="btn btn-ghost"
              onClick={() => setShowAllMisc((v) => !v)}
              style={{ marginTop: 8, fontSize: 13 }}
            >
              {showAllMisc ? 'Show less' : `See all ${data!.top_misclassifications.length}`}
            </button>
          )}
        </div>
      )}

      {/* Data honesty footer */}
      <div className="data-honesty-footer" role="note">
        <span style={{ fontSize: 16, flexShrink: 0 }} aria-hidden="true">ℹ</span>
        <span>
          These figures show items classified through LoopWise. They do not represent
          every item sorted across the ward — only what was scanned or described using this app.
        </span>
      </div>
    </div>
  );
}

interface SummaryCardProps {
  label: string;
  value: string;
  sub: string;
  signal?: 'good' | 'warn' | 'bad';
}

function SummaryCard({ label, value, sub, signal }: SummaryCardProps) {
  const valueColor = signal === 'good'
    ? 'var(--color-signal-good)'
    : signal === 'warn'
    ? 'var(--color-signal-warn)'
    : signal === 'bad'
    ? 'var(--color-signal-bad)'
    : 'var(--color-text-primary)';

  return (
    <div className="card">
      <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--color-text-secondary)', marginBottom: 8 }}>
        {label}
      </div>
      <div
        style={{
          fontFamily: 'var(--font-display)',
          fontSize: 32,
          fontWeight: 700,
          color: valueColor,
          lineHeight: 1,
          marginBottom: 6,
        }}
        className="tabular-nums"
      >
        {value}
      </div>
      <div style={{ fontSize: 12, color: 'var(--color-text-tertiary)', lineHeight: 1.4 }}>{sub}</div>
    </div>
  );
}
