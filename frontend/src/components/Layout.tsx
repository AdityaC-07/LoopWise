import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  Camera,
  LayoutGrid,
  MapPin,
  HelpCircle,
  ChevronLeft,
  ChevronRight,
  Recycle,
} from 'lucide-react';
import { PracticeModeIndicator } from './PracticeModeIndicator';

const NAV_ITEMS = [
  { to: '/classify', label: 'Classify Waste', icon: Camera },
  { to: '/analytics', label: 'Overview', icon: LayoutGrid },
  { to: '/analytics/ward/WD-DEMO-A', label: 'My Ward', icon: MapPin },
  { to: '/help', label: 'Help', icon: HelpCircle },
];

interface LayoutProps {
  children: React.ReactNode;
  demoMode?: boolean;
}

export function Layout({ children, demoMode }: LayoutProps) {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  return (
    <>
      {/* Top bar */}
      <header className="topbar" role="banner">
        <NavLink
          to="/classify"
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
              color: 'var(--color-text-primary)',
            }}
          >
            LoopWise
          </span>
        </NavLink>
        <div style={{ flex: 1 }} />
        <PracticeModeIndicator demoMode={demoMode} />
      </header>

      {/* Desktop sidebar */}
      <nav
        className={`sidebar ${collapsed ? 'collapsed' : ''}`}
        aria-label="Main navigation"
        style={{ display: undefined }}
      >
        <ul style={{ listStyle: 'none', margin: 0, padding: 0, flex: 1 }}>
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => {
            const isActive =
              to === '/classify'
                ? location.pathname === '/classify' || location.pathname === '/' || location.pathname.startsWith('/result')
                : location.pathname.startsWith(to);
            return (
              <li key={to}>
                <NavLink
                  to={to}
                  className={`nav-item ${isActive ? 'active' : ''}`}
                  title={collapsed ? label : undefined}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <Icon size={20} aria-hidden="true" style={{ flexShrink: 0 }} />
                  {!collapsed && <span>{label}</span>}
                </NavLink>
              </li>
            );
          })}
        </ul>

        <button
          className="nav-item"
          onClick={() => setCollapsed((v) => !v)}
          aria-label={collapsed ? 'Expand navigation' : 'Collapse navigation'}
          style={{ borderTop: '1px solid var(--color-border)', marginTop: 'auto' }}
        >
          {collapsed ? (
            <ChevronRight size={18} aria-hidden="true" />
          ) : (
            <>
              <ChevronLeft size={18} aria-hidden="true" />
              <span>Collapse</span>
            </>
          )}
        </button>
      </nav>

      {/* Mobile bottom tab bar */}
      <nav className="tabbar" aria-label="Mobile navigation" style={{ display: undefined }}>
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => {
          const isActive =
            to === '/classify'
              ? location.pathname === '/classify' || location.pathname === '/' || location.pathname.startsWith('/result')
              : location.pathname.startsWith(to);
          return (
            <NavLink
              key={to}
              to={to}
              className={`tab-item ${isActive ? 'active' : ''}`}
              aria-label={label}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon size={22} aria-hidden="true" />
              <span>{label.split(' ')[0]}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Page content */}
      <main
        id="main-content"
        className={`page-content ${collapsed ? 'sidebar-collapsed' : ''}`}
      >
        {children}
      </main>
    </>
  );
}
