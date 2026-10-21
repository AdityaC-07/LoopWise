import { Link } from 'react-router-dom';
import { useTour, Tour } from '../components/Tour';
import { PlayCircle, Camera, LayoutGrid, MapPin } from 'lucide-react';
import { useEffect, useState } from 'react';
import { getMaterials } from '../api/client';
import { LoadingDots } from '../components/Loading';
import { MaterialBadge } from '../components/MaterialBadge';
import { friendlyBinLabel, binColor } from '../utils/display';
import type { Material } from '../types/api';

const CATEGORIES = ['all', 'plastic', 'paper', 'organic', 'glass', 'metal', 'ewaste', 'other'];

export default function HelpPage() {
  const { showTour, startTour, closeTour } = useTour();
  const [materials, setMaterials] = useState<Material[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    getMaterials()
      .then((r) => setMaterials(r.data))
      .catch(() => {/* fail silently */})
      .finally(() => setLoading(false));
  }, []);

  const filtered = selectedCategory === 'all'
    ? materials
    : materials.filter((m) => m.category.toLowerCase() === selectedCategory);

  return (
    <>
      {showTour && <Tour onClose={closeTour} />}

      <div className="content-area">
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 28,
            fontWeight: 600,
            color: 'var(--color-text-primary)',
            margin: '0 0 24px',
          }}
        >
          Help
        </h1>

        {/* Replay tour card */}
        <button
          id="nav-help"
          className="card card-interactive"
          onClick={startTour}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 16,
            width: '100%',
            textAlign: 'left',
            marginBottom: 32,
            cursor: 'pointer',
            border: 'none',
          }}
          aria-label="Replay the app tour"
        >
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: 'var(--radius-md)',
              background: 'var(--color-amber-dim)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
            aria-hidden="true"
          >
            <PlayCircle size={24} style={{ color: 'var(--color-amber)' }} />
          </div>
          <div>
            <div style={{ fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 4 }}>
              Replay the app tour
            </div>
            <div style={{ fontSize: 14, color: 'var(--color-text-secondary)' }}>
              Walk through how LoopWise works
            </div>
          </div>
        </button>

        {/* How to use cards */}
        <div className="section-label">How to use LoopWise</div>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: 'var(--card-gap)',
            marginBottom: 32,
          }}
        >
          <Link to="/classify" className="card card-interactive" style={{ textDecoration: 'none', display: 'flex', gap: 12, alignItems: 'flex-start' }}>
            <Camera size={20} style={{ color: 'var(--color-amber)', flexShrink: 0, marginTop: 2 }} aria-hidden="true" />
            <div>
              <div style={{ fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 4 }}>Classify waste</div>
              <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
                Take a photo or describe an item to find out which bin it belongs in.
              </div>
            </div>
          </Link>
          <Link to="/analytics" className="card card-interactive" style={{ textDecoration: 'none', display: 'flex', gap: 12, alignItems: 'flex-start' }}>
            <LayoutGrid size={20} style={{ color: 'var(--color-amber)', flexShrink: 0, marginTop: 2 }} aria-hidden="true" />
            <div>
              <div style={{ fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 4 }}>View analytics</div>
              <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
                See how waste sorting is going across your ward and area.
              </div>
            </div>
          </Link>
          <Link to="/analytics/ward/WD-DEMO-A" className="card card-interactive" style={{ textDecoration: 'none', display: 'flex', gap: 12, alignItems: 'flex-start' }}>
            <MapPin size={20} style={{ color: 'var(--color-amber)', flexShrink: 0, marginTop: 2 }} aria-hidden="true" />
            <div>
              <div style={{ fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 4 }}>My ward</div>
              <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
                Detailed data for your assigned ward.
              </div>
            </div>
          </Link>
        </div>

        {/* Material guide */}
        <div style={{ marginBottom: 24 }}>
          <div className="section-label">Material guide</div>
          <p style={{ fontSize: 15, color: 'var(--color-text-secondary)', margin: '0 0 16px' }}>
            Quick reference for common items.
          </p>

          {/* Category filter */}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }} role="group" aria-label="Filter by category">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                className={selectedCategory === cat ? 'btn btn-primary' : 'btn btn-secondary'}
                style={{ fontSize: 12, padding: '4px 12px', height: 30, minWidth: 'unset' }}
                onClick={() => setSelectedCategory(cat)}
                aria-pressed={selectedCategory === cat}
              >
                {cat === 'all' ? 'All' : cat.charAt(0).toUpperCase() + cat.slice(1)}
              </button>
            ))}
          </div>

          {loading ? (
            <LoadingDots label="Loading guide…" />
          ) : (
            <div
              style={{
                background: 'var(--color-surface-1)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--card-radius)',
                overflow: 'hidden',
              }}
            >
              {filtered.slice(0, 30).map((mat, idx) => {
                const isExp = expandedId === mat.material_id;
                const col = binColor(mat.disposal_bin);
                return (
                  <div key={mat.material_id} style={{ borderBottom: idx === filtered.length - 1 ? 'none' : '1px solid var(--color-border)' }}>
                    <button
                      onClick={() => setExpandedId(isExp ? null : mat.material_id)}
                      aria-expanded={isExp}
                      style={{
                        width: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 10,
                        padding: '12px 16px',
                        background: isExp ? 'var(--color-surface-3)' : 'transparent',
                        border: 'none',
                        cursor: 'pointer',
                        textAlign: 'left',
                        color: 'var(--color-text-primary)',
                        transition: 'background 150ms ease',
                      }}
                    >
                      <MaterialBadge category={mat.category} />
                      <span style={{ flex: 1, fontWeight: 500, fontSize: 14 }}>{mat.name}</span>
                      <span style={{ fontSize: 12, color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'center', gap: 5, flexShrink: 0 }}>
                        <span style={{ width: 8, height: 8, borderRadius: '50%', background: col, display: 'inline-block' }} aria-hidden="true" />
                        {friendlyBinLabel(mat.disposal_bin)}
                      </span>
                      <span style={{ fontSize: 12, color: 'var(--color-text-tertiary)', flexShrink: 0 }}>
                        {mat.recovery_potential.charAt(0).toUpperCase() + mat.recovery_potential.slice(1)} ♻
                      </span>
                    </button>
                    {isExp && (
                      <div style={{ padding: '0 16px 14px', background: 'var(--color-surface-2)', borderTop: '1px solid var(--color-border)', fontSize: 14, color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
                        <div style={{ paddingTop: 12 }}>
                          {mat.next_life && <p style={{ margin: '0 0 6px' }}><strong style={{ color: 'var(--color-text-primary)' }}>What happens next:</strong> {mat.next_life}</p>}
                          {mat.contamination_notes && <p style={{ margin: '0' }}><strong style={{ color: 'var(--color-text-primary)' }}>Note:</strong> {mat.contamination_notes}</p>}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
