import { useEffect, useMemo, useState } from 'react';
import { Search, ChevronDown, ChevronUp, Trash2 } from 'lucide-react';
import { getMaterials } from '../api/client';
import { LoadingDots } from '../components/Loading';
import { ErrorMessage, EmptyState } from '../components/ErrorMessage';
import { MaterialBadge } from '../components/MaterialBadge';
import { friendlyBinLabel, binColor, recoveryLabel, filterMaterials } from '../utils/display';
import type { Material } from '../types/api';

const CATEGORIES = ['all', 'plastic', 'paper', 'organic', 'glass', 'metal', 'ewaste', 'hazardous', 'composite', 'other'];

export default function MaterialsPage() {
  const [materials, setMaterials] = useState<Material[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    getMaterials()
      .then((r) => setMaterials(r.data))
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(
    () => filterMaterials(materials, search, category),
    [materials, search, category]
  );

  if (loading) return <div className="content-area"><LoadingDots label="Loading materials guide…" /></div>;

  return (
    <div className="content-area">
      <h1
        style={{
          fontFamily: 'var(--font-display)',
          fontSize: 28,
          fontWeight: 600,
          color: 'var(--color-text-primary)',
          margin: '0 0 8px',
        }}
      >
        Materials Guide
      </h1>
      <p style={{ color: 'var(--color-text-secondary)', fontSize: 15, margin: '0 0 24px' }}>
        Quick reference for common items and where they belong.
      </p>

      {error && (
        <div style={{ marginBottom: 16 }}>
          <ErrorMessage message={error} onRetry={() => window.location.reload()} />
        </div>
      )}

      {/* Search */}
      <div style={{ position: 'relative', marginBottom: 16 }}>
        <Search
          size={16}
          style={{
            position: 'absolute',
            left: 12,
            top: '50%',
            transform: 'translateY(-50%)',
            color: 'var(--color-text-tertiary)',
          }}
          aria-hidden="true"
        />
        <input
          type="search"
          className="input-field"
          placeholder="Search materials…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ paddingLeft: 36 }}
          aria-label="Search materials by name or category"
        />
      </div>

      {/* Category filter */}
      <div
        style={{
          display: 'flex',
          gap: 8,
          flexWrap: 'wrap',
          marginBottom: 24,
        }}
        role="group"
        aria-label="Filter by material category"
      >
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setCategory(cat)}
            className={category === cat ? 'btn btn-primary' : 'btn btn-secondary'}
            style={{
              fontSize: 13,
              padding: '6px 14px',
              height: 34,
              minWidth: 'unset',
            }}
            aria-pressed={category === cat}
          >
            {cat === 'all' ? 'All' : cat.charAt(0).toUpperCase() + cat.slice(1)}
          </button>
        ))}
      </div>

      {/* Results count */}
      <div style={{ fontSize: 13, color: 'var(--color-text-tertiary)', marginBottom: 12 }}>
        {filtered.length} item{filtered.length !== 1 ? 's' : ''} found
      </div>

      {/* Materials list */}
      {filtered.length === 0 ? (
        <EmptyState
          icon={<Search size={40} />}
          title="No materials found"
          body={`Try a different search term or select a different category.`}
        />
      ) : (
        <div
          style={{
            background: 'var(--color-surface-1)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--card-radius)',
            overflow: 'hidden',
          }}
        >
          {filtered.map((mat, idx) => (
            <MaterialRow
              key={mat.material_id}
              material={mat}
              isLast={idx === filtered.length - 1}
              expanded={expandedId === mat.material_id}
              onToggle={() =>
                setExpandedId(expandedId === mat.material_id ? null : mat.material_id)
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface MaterialRowProps {
  material: Material;
  isLast: boolean;
  expanded: boolean;
  onToggle: () => void;
}

function MaterialRow({ material: mat, isLast, expanded, onToggle }: MaterialRowProps) {
  const binCol = binColor(mat.disposal_bin);
  const recLabel = recoveryLabel(mat.recovery_potential);

  return (
    <div style={{ borderBottom: isLast ? 'none' : '1px solid var(--color-border)' }}>
      <button
        onClick={onToggle}
        aria-expanded={expanded}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          padding: '14px 16px',
          background: expanded ? 'var(--color-surface-3)' : 'transparent',
          border: 'none',
          cursor: 'pointer',
          textAlign: 'left',
          transition: 'background-color 150ms ease',
          color: 'var(--color-text-primary)',
        }}
      >
        <MaterialBadge category={mat.category} />
        <span style={{ flex: 1, fontWeight: 500, fontSize: 14 }}>{mat.name}</span>
        <span style={{ fontSize: 13, color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: binCol, display: 'inline-block' }} aria-hidden="true" />
          {friendlyBinLabel(mat.disposal_bin)}
        </span>
        <span style={{ fontSize: 13, color: 'var(--color-text-secondary)', minWidth: 80, textAlign: 'right', flexShrink: 0 }}>
          {recLabel}
        </span>
        {expanded ? (
          <ChevronUp size={16} style={{ color: 'var(--color-text-tertiary)', flexShrink: 0 }} aria-hidden="true" />
        ) : (
          <ChevronDown size={16} style={{ color: 'var(--color-text-tertiary)', flexShrink: 0 }} aria-hidden="true" />
        )}
      </button>

      {expanded && (
        <div
          style={{
            padding: '0 16px 16px 16px',
            background: 'var(--color-surface-2)',
            borderTop: '1px solid var(--color-border)',
          }}
        >
          <div style={{ paddingTop: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
            {mat.next_life && (
              <div>
                <div className="section-label">What happens next</div>
                <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', margin: 0 }}>{mat.next_life}</p>
              </div>
            )}
            {mat.recovery_channel && (
              <div>
                <div className="section-label">Recovery channel</div>
                <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', margin: 0 }}>{mat.recovery_channel}</p>
              </div>
            )}
            {mat.contamination_notes && (
              <div>
                <div className="section-label">Important notes</div>
                <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', margin: 0 }}>{mat.contamination_notes}</p>
              </div>
            )}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Trash2 size={16} style={{ color: binCol }} aria-hidden="true" />
              <span style={{ fontSize: 14, fontWeight: 600, color: binCol }}>
                {friendlyBinLabel(mat.disposal_bin)}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
