// LoopWise API type definitions
// These match the exact backend response schemas in backend/app/api/

export interface ApiEnvelope<T> {
  status: 'ok' | 'error';
  data: T;
  error: { code: string; message: string } | null;
  meta: {
    request_id: string;
    model_version: string;
  };
}

// ── Classify ────────────────────────────────────────────────
export interface ConsentPayload {
  image_upload: boolean;
  analytics: boolean;
  location: boolean;
}

export interface ClassifyRequest {
  session_id: string;
  input_type: 'image' | 'text';
  image_b64?: string;
  description?: string;
  ward_id?: string;
  consent: ConsentPayload;
}

export interface Top3Item {
  class: string;
  confidence: number;
}

export interface MaterialDetail {
  name: string;
  category: string;
  disposal_bin: string;
  recovery_potential: string;
  next_life: string;
  recovery_channel: string;
  contamination_notes: string;
}

export interface GuidanceDetail {
  bin_label: string;
  action: string;
  do: string[];
  do_not: string[];
}

export interface ClassifyResult {
  event_id: string;
  predicted_class: string;
  confidence: number;
  confidence_label: string;
  top3: Top3Item[];
  material: MaterialDetail;
  guidance: GuidanceDetail;
}

// ── Feedback ────────────────────────────────────────────────
export interface FeedbackRequest {
  event_id: string;
  session_id: string;
  feedback_type: 'correction' | 'confirmation';
  corrected_class?: string;
  note?: string;
}

export interface FeedbackResult {
  correction_id: string | null;
  acknowledged: boolean;
}

// ── Materials ────────────────────────────────────────────────
export interface Material {
  material_id: string;
  name: string;
  category: string;
  subcategory?: string;
  disposal_bin: string;
  recovery_potential: string;
  next_life?: string;
  recovery_channel?: string;
  contamination_notes?: string;
  icon_slug?: string;
  demo_seed: boolean;
}

// ── Analytics ───────────────────────────────────────────────
export interface AnalyticsPeriod {
  from: string;
  to: string;
}

export interface AnalyticsSummary {
  total_events: number;
  correction_rate: number;
  contamination_rate: number;
  recovery_potential_avg: number;
  low_confidence_rate: number;
}

export interface TimeseriesPoint {
  date: string;
  total_events: number;
  correction_rate: number;
  contamination_rate: number;
  recovery_potential_avg: number;
}

export interface MisclassificationItem {
  predicted: string;
  corrected: string;
  count: number;
}

export interface WardAnalytics {
  ward_id: string;
  period: AnalyticsPeriod;
  demo_data: boolean;
  summary: AnalyticsSummary;
  timeseries: TimeseriesPoint[];
  material_breakdown: Record<string, number>;
  top_misclassifications: MisclassificationItem[];
}

export interface OverviewAnalytics {
  period: AnalyticsPeriod;
  demo_data: boolean;
  summary: AnalyticsSummary;
  material_breakdown: Record<string, number>;
  top_misclassifications: MisclassificationItem[];
}

// ── Health ────────────────────────────────────────────────
// Matches backend GET /api/v1/health (app/api/routers/health.py)
export interface HealthData {
  status: string;
  components?: {
    database: string;
    inference_engine: string;
    cache: string;
    image_store: string;
  };
  model_version?: string;
  environment?: string;
  inference_error?: string;
}
