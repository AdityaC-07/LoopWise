import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { BinCard } from '../components/BinCard';
import { ConfidenceBar } from '../components/ConfidenceBar';
import { MaterialBadge } from '../components/MaterialBadge';
import { StatusLight } from '../components/StatusLight';
import { ErrorMessage, EmptyState } from '../components/ErrorMessage';
import { ServiceStatusIndicator } from '../components/ServiceStatusIndicator';
import LandingPage from '../pages/LandingPage';

describe('LandingPage', () => {
  it('routes every "Identify an item" CTA to the classifier', () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    );
    const links = screen.getAllByRole('link', { name: /identify an item/i });
    expect(links.length).toBeGreaterThan(0);
    for (const link of links) {
      expect(link.getAttribute('href')).toBe('/classify');
    }
  });

  it('routes dashboard CTAs to real destinations', () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    );
    const links = screen.getAllByRole('link', { name: /dashboard/i });
    expect(links.length).toBeGreaterThan(0);
    for (const link of links) {
      const href = link.getAttribute('href') ?? '';
      expect(
        href === '/analytics' ||
        href.startsWith('/analytics/') ||
        href.startsWith('#')
      ).toBe(true);
    }
  });

  it('labels the example result as illustrative, not a live prediction', () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    );
    expect(screen.getAllByText(/illustrative example/i).length).toBeGreaterThan(0);
    expect(screen.getByText('Example')).toBeDefined();
  });

  it('shows the category before the bin in the showcase', () => {
    const { container } = render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    );
    const text = container.textContent ?? '';
    const catIdx = text.indexOf('Waste category');
    const binIdx = text.indexOf('Where it goes');
    expect(catIdx).toBeGreaterThan(-1);
    expect(binIdx).toBeGreaterThan(catIdx);
  });
});

describe('BinCard', () => {
  it('renders bin label and action', () => {
    render(<BinCard disposalBin="wet" action="Place directly into the green wet waste bin." />);
    expect(screen.getByText('Green Wet Waste Bin')).toBeDefined();
    expect(screen.getByText('Place directly into the green wet waste bin.')).toBeDefined();
  });

  it('renders the same content in compact mode with reduced icon size', () => {
    const { container } = render(
      <BinCard disposalBin="dry" action="Rinse and place in the dry waste bin." compact />
    );
    expect(screen.getByText('Blue Dry Waste Bin')).toBeDefined();
    expect(screen.getByText('Rinse and place in the dry waste bin.')).toBeDefined();
    const svg = container.querySelector('svg');
    expect(svg?.getAttribute('width')).toBe('18');
  });
});

describe('ConfidenceBar', () => {
  it('renders plain language label', () => {
    render(<ConfidenceBar confidence={0.9} confidenceLabel="Very sure" />);
    expect(screen.getByText('Very sure')).toBeDefined();
    expect(screen.getByText('How sure we are')).toBeDefined();
  });

  it('renders medium confidence label', () => {
    render(<ConfidenceBar confidence={0.65} confidenceLabel="Fairly sure" />);
    expect(screen.getByText('Fairly sure')).toBeDefined();
  });

  it('renders low confidence label', () => {
    render(<ConfidenceBar confidence={0.3} confidenceLabel="Not very sure" />);
    expect(screen.getByText('Not very sure')).toBeDefined();
  });

  it('does not display numeric confidence score', () => {
    const { container } = render(<ConfidenceBar confidence={0.876} confidenceLabel="Very sure" />);
    expect(container.textContent).not.toContain('0.876');
    expect(container.textContent).not.toContain('87.6');
    expect(container.textContent).not.toContain('88%');
  });
});

describe('MaterialBadge', () => {
  it('renders category name', () => {
    render(<MaterialBadge category="plastic" />);
    expect(screen.getByText('plastic')).toBeDefined();
  });

  it('renders organic category', () => {
    render(<MaterialBadge category="organic" />);
    expect(screen.getByText('organic')).toBeDefined();
  });
});

describe('StatusLight', () => {
  it('shows label text alongside indicator', () => {
    render(<StatusLight contaminationRate={0.05} />);
    expect(screen.getByText('Excellent')).toBeDefined();
  });

  it('shows needs work for high contamination', () => {
    render(<StatusLight contaminationRate={0.25} />);
    expect(screen.getByText('Needs work')).toBeDefined();
  });

  it('can hide label', () => {
    render(<StatusLight contaminationRate={0.25} showLabel={false} />);
    expect(screen.queryByText('Needs work')).toBeNull();
  });
});

describe('ErrorMessage', () => {
  it('renders the error message text', () => {
    render(<ErrorMessage message="We couldn't connect. Please check your internet." />);
    expect(screen.getByText("We couldn't connect. Please check your internet.")).toBeDefined();
  });

  it('has correct ARIA role', () => {
    render(<ErrorMessage message="Something went wrong." />);
    expect(screen.getByRole('alert')).toBeDefined();
  });

  it('shows retry button when onRetry is provided', () => {
    render(<ErrorMessage message="Error" onRetry={() => {}} />);
    expect(screen.getByText('Try again')).toBeDefined();
  });

  it('hides retry button when onRetry is not provided', () => {
    render(<ErrorMessage message="Error" />);
    expect(screen.queryByText('Try again')).toBeNull();
  });
});

describe('EmptyState', () => {
  it('renders title and body', () => {
    render(<EmptyState title="No data" body="Try a different range." />);
    expect(screen.getByText('No data')).toBeDefined();
    expect(screen.getByText('Try a different range.')).toBeDefined();
  });

  it('renders action when provided', () => {
    render(
      <EmptyState
        title="Empty"
        body="Nothing here"
        action={<button>Go back</button>}
      />
    );
    expect(screen.getByText('Go back')).toBeDefined();
  });
});

describe('ServiceStatusIndicator', () => {
  it('reports readiness from backend health, not a hardcoded flag', () => {
    const { rerender } = render(<ServiceStatusIndicator status="unavailable" />);
    expect(screen.getByText('Image recognition unavailable')).toBeDefined();
    expect(screen.getByRole('status').getAttribute('data-status')).toBe('unavailable');

    rerender(<ServiceStatusIndicator status="ready" />);
    expect(screen.getByText('Image recognition ready')).toBeDefined();
    expect(screen.getByRole('status').getAttribute('data-status')).toBe('ready');
  });

  it('renders nothing while health status is still unknown', () => {
    const { container } = render(<ServiceStatusIndicator status="unknown" />);
    expect(container.textContent).toBe('');
  });

  it('contains no practice-mode wording', () => {
    render(<ServiceStatusIndicator status="ready" />);
    expect(screen.queryByText(/practice/i)).toBeNull();
    expect(screen.queryByText(/not live data/i)).toBeNull();
  });
});
