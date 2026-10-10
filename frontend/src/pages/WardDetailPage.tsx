import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ReferenceLine, ResponsiveContainer,
  BarChart, Bar, Cell, Legend,
} from 'recharts';
import { ArrowLeft, Calendar } from 'lucide-react';
import { getWardAnalytics } from '../api/client';
import { LoadingDots, ChartSkeleton } from '../components/Loading';
import { ErrorMessage, EmptyState } from '../components/ErrorMessage';
import { formatNumber, formatPercent, friendlyWardName, dateNDaysAgo, todayIso } from '../utils/display';
import type { WardAnalytics } from '../types/api';

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

type DateRange = '7' | '30' | '90';

export default function WardDetailPage() {
  const { wardId = 'WD-DEMO-A' } = useParams<{ wardId: string }>();
  const [data, setData] = useState<WardAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [range, setRange] = useState<DateRange>('30');
  const [showAllMisc, setShowAllMisc] = useState(false);

  function fetchData(days: string) {
    setLoading(true);
    setError(null);
    getWardAnalytics(wardId, {
      date_from: dateNDaysAgo(Number(days)),
      date_to: todayIso(),
      aggregation: 'day',
    })
      .then((r) => setData(r.data))
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => { fetchData(range); }, [wardId, range]);

  const wardName = friendlyWardName(wardId);

  const tsData = data?.timeseries.map((p) => ({
    date: p.date.slice(5), // MM-DD
    wronglySorted: Math.round(p.contamination_rate * 100),
    recyclingOpportunity: Math.round(p.recovery_potential_avg * 100),
  })) ?? [];

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
    <div className="content-area">
      {/* Breadcrumb */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16, fontSize: 14, color: 'var(--color-text-secondary)' }}>
        <Link to="/analytics" className="btn btn-ghost" style={{ padding: '4px 0', fontSize: 14, gap: 4 }}>
          <ArrowLeft size={14} aria-hidden="true" />
          Overview
        </Link>
        <span aria-hidden="true">›</span>
        <span style={{ color: 'var(--color-text-primary)', fontWeight: 500 }}>{wardName}</span>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 12, marginBottom: 32 }}>
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 28,
            fontWeight: 600,
            color: 'var(--color-text-primary)',
            margin: 0,
            flex: 1,
          }}
        >
          {wardName}
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
            }}
          >
            Demo data
          </span>
        )}

        {/* Date range selector */}
        <div
          style={{ display: 'flex', gap: 8, alignItems: 'center' }}
          role="group"
          aria-label="Select time period"
        >
          <Calendar size={14} style={{ color: 'var(--color-text-tertiary)' }} aria-hidden="true" />
          {(['7', '30', '90'] as DateRange[]).map((d) => (
            <button
              key={d}
              className={range === d ? 'btn btn-primary' : 'btn btn-secondary'}
              style={{ fontSize: 13, padding: '6px 12px', height: 32, minWidth: 'unset' }}
              onClick={() => setRange(d)}
              aria-pressed={range === d}
            >
              {d === '7' ? 'Last 7 days' : d === '30' ? 'Last 30 days' : 'Last 90 days'}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div style={{ marginBottom: 24 }}>
          <ErrorMessage message={error} onRetry={() => fetchData(range)} />
        </div>
      )}

      {loading ? (
        <LoadingDots label="Loading ward data…" />
      ) : !data || data.timeseries.length === 0 ? (
        <EmptyState
          icon={
            <svg width="64" height="64" viewBox="0 0 64 64" fill="none" aria-hidden="true">
              <circle cx="32" cy="32" r="20" stroke="var(--color-amber)" strokeWidth="2" strokeDasharray="4 4" />
              <circle cx="32" cy="32" r="10" stroke="var(--color-amber)" strokeWidth="1.5" opacity="0.5" />
              <circle cx="32" cy="32" r="4" fill="var(--color-amber)" opacity="0.5" />
            </svg>
          }
          title="No data for this period"
          body="Try a different date range, or check that this ward has been active."
          action={
            <Link to="/analytics" className="btn btn-secondary" style={{ marginTop: 8 }}>
              ← Back to Overview
            </Link>
          }
        />
      ) : (
        <>
          {/* Summary cards */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: 'var(--card-gap)',
              marginBottom: 32,
            }}
          >
            <SummaryCard label="Items sorted" value={formatNumber(data.summary.total_events)} sub="Total classifications this period" />
            <SummaryCard
              label="Wrongly sorted"
              value={formatPercent(data.summary.contamination_rate)}
              sub="Items put in the wrong bin"
              signal={data.summary.contamination_rate > 0.2 ? 'bad' : data.summary.contamination_rate > 0.1 ? 'warn' : 'good'}
            />
            <SummaryCard
              label="Recycling opportunity"
              value={formatPercent(data.summary.recovery_potential_avg)}
              sub="How recyclable the sorted items are"
            />
            <SummaryCard
              label="Uncertain answers"
              value={formatPercent(data.summary.low_confidence_rate)}
              sub="Items we weren't confident about"
            />
          </div>

          {/* Timeseries chart */}
          <div style={{ marginBottom: 32 }}>
            <div className="section-label">How sorting is changing over time</div>
            <div className="card">
              {tsData.length === 0 ? (
                <ChartSkeleton />
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={tsData} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
                    <title>Sorting trends over time</title>
                    <XAxis
                      dataKey="date"
                      tick={{ fill: 'var(--color-text-tertiary)', fontSize: 11 }}
                      interval={tsData.length > 14 ? Math.floor(tsData.length / 7) : 0}
                    />
                    <YAxis
                      unit="%"
                      domain={[0, 100]}
                      tick={{ fill: 'var(--color-text-tertiary)', fontSize: 11 }}
                      label={{
                        value: 'Proportion of items sorted (%)',
                        angle: -90,
                        position: 'insideLeft',
                        fill: 'var(--color-text-tertiary)',
                        fontSize: 11,
                        dy: 60,
                      }}
                    />
                    <Tooltip
                      contentStyle={{
                        background: 'var(--color-surface-1)',
                        border: '1px solid var(--color-border)',
                        borderRadius: 'var(--radius-md)',
                        color: 'var(--color-text-primary)',
                        fontSize: 13,
                      }}
                      formatter={(val: unknown, name: unknown) => [
                        `${val as number}%`,
                        name === 'wronglySorted' ? 'Wrongly sorted' : 'Recycling opportunity',
                      ]}
                      labelFormatter={(label) => `Date: ${label}`}
                    />
                    <ReferenceLine
                      y={20}
                      stroke="var(--color-signal-warn)"
                      strokeDasharray="4 4"
                      label={{
                        value: '20% threshold — needs attention',
                        fill: 'var(--color-signal-warn)',
                        fontSize: 11,
                        position: 'insideTopRight',
                      }}
                    />
                    <Legend
                      formatter={(val) =>
                        val === 'wronglySorted' ? 'Wrongly sorted' : 'Recycling opportunity'
                      }
                      wrapperStyle={{ color: 'var(--color-text-secondary)', fontSize: 13 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="wronglySorted"
                      stroke="var(--color-signal-bad)"
                      strokeWidth={2}
                      dot={false}
                      animationDuration={600}
                    />
                    <Line
                      type="monotone"
                      dataKey="recyclingOpportunity"
                      stroke="var(--color-signal-good)"
                      strokeWidth={2}
                      dot={false}
                      animationDuration={600}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Material breakdown */}
          {matBreakdownData.length > 0 && (
            <div style={{ marginBottom: 32 }}>
              <div className="section-label">What's being sorted</div>
              <div className="card">
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart
                    data={matBreakdownData}
                    layout="vertical"
                    margin={{ top: 0, right: 16, bottom: 0, left: 16 }}
                  >
                    <title>Material breakdown</title>
                    <XAxis type="number" unit="%" tick={{ fill: 'var(--color-text-tertiary)', fontSize: 11 }} />
                    <YAxis type="category" dataKey="name" width={70} tick={{ fill: 'var(--color-text-secondary)', fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{
                        background: 'var(--color-surface-1)',
                        border: '1px solid var(--color-border)',
                        borderRadius: 'var(--radius-md)',
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
              </div>
            </div>
          )}

          {/* Commonly confused items */}
          {visibleMisc.length > 0 && (
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
                <button className="btn btn-ghost" onClick={() => setShowAllMisc((v) => !v)} style={{ marginTop: 8, fontSize: 13 }}>
                  {showAllMisc ? 'Show less' : 'See all'}
                </button>
              )}
            </div>
          )}

          {/* Data honesty footer */}
          <div className="data-honesty-footer" role="note">
            <span style={{ fontSize: 16, flexShrink: 0 }} aria-hidden="true">ℹ</span>
            <span>
              These figures show items classified through LoopWise. They do not represent every item sorted across the ward — only what was scanned or described using this app.
            </span>
          </div>
        </>
      )}
    </div>
  );
}

function SummaryCard({ label, value, sub, signal }: { label: string; value: string; sub: string; signal?: 'good' | 'warn' | 'bad' }) {
  const valueColor = signal === 'good'
    ? 'var(--color-signal-good)'
    : signal === 'warn'
    ? 'var(--color-signal-warn)'
    : signal === 'bad'
    ? 'var(--color-signal-bad)'
    : 'var(--color-text-primary)';
  return (
    <div className="card">
      <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--color-text-secondary)', marginBottom: 8 }}>{label}</div>
      <div style={{ fontFamily: 'var(--font-display)', fontSize: 30, fontWeight: 700, color: valueColor, lineHeight: 1, marginBottom: 6 }} className="tabular-nums">{value}</div>
      <div style={{ fontSize: 12, color: 'var(--color-text-tertiary)', lineHeight: 1.4 }}>{sub}</div>
    </div>
  );
}
