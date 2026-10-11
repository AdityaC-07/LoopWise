import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ConfidenceBar } from '../components/ConfidenceBar';
import { MaterialBadge } from '../components/MaterialBadge';
import { StatusLight } from '../components/StatusLight';
import { ErrorMessage, EmptyState } from '../components/ErrorMessage';
import { PracticeModeIndicator, PracticeModeTooltip } from '../components/PracticeModeIndicator';

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

  describe('Practice mode indicators', () => {
    it('only renders the top-bar indicator when demo mode is active', () => {
      const { rerender } = render(<PracticeModeIndicator demoMode={false} />);
      expect(screen.queryByText('Practice Mode — not live data')).toBeNull();

      rerender(<PracticeModeIndicator demoMode />);
      expect(screen.getByText('Practice Mode — not live data')).toBeDefined();
    });

    it('does not show the classify warning for real inference', () => {
      const { rerender } = render(<PracticeModeTooltip demoMode={false} />);
      expect(screen.queryByText('Practice Mode')).toBeNull();

      rerender(<PracticeModeTooltip demoMode />);
      expect(screen.getByText('Practice Mode')).toBeDefined();
    });
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
