import type {
  ApiEnvelope,
  ClassifyRequest,
  ClassifyResult,
  FeedbackRequest,
  FeedbackResult,
  Material,
  WardAnalytics,
  OverviewAnalytics,
  HealthData,
} from '../types/api';

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://127.0.0.1:8000';

class ApiError extends Error {
  code: string;
  status?: number;

  constructor(
    code: string,
    message: string,
    status?: number
  ) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<ApiEnvelope<T>> {
  const url = `${BASE_URL}${path}`;
  let res: Response;
  try {
    res = await fetch(url, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    });
  } catch {
    throw new ApiError('NETWORK_ERROR', "We couldn't connect. Please check your internet and try again.");
  }

  const json = await res.json() as ApiEnvelope<T>;

  if (!res.ok || json.status === 'error') {
    const errCode = json.error?.code ?? 'UNKNOWN';
    const errMsg = json.error?.message ?? 'Something went wrong. Please try again.';
    throw new ApiError(errCode, errMsg, res.status);
  }

  return json;
}

// ── Health ─────────────────────────────────────────────────
export async function getHealth(): Promise<ApiEnvelope<HealthData>> {
  return request<HealthData>('/api/v1/health');
}

// ── Classify ────────────────────────────────────────────────
export async function classifyItem(
  payload: ClassifyRequest
): Promise<ApiEnvelope<ClassifyResult>> {
  return request<ClassifyResult>('/api/v1/classify', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// ── Feedback ────────────────────────────────────────────────
export async function submitFeedback(
  payload: FeedbackRequest
): Promise<ApiEnvelope<FeedbackResult>> {
  return request<FeedbackResult>('/api/v1/feedback', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// ── Materials ────────────────────────────────────────────────
export async function getMaterials(): Promise<ApiEnvelope<Material[]>> {
  return request<Material[]>('/api/v1/materials');
}

// ── Analytics ────────────────────────────────────────────────
export async function getAnalyticsOverview(): Promise<ApiEnvelope<OverviewAnalytics>> {
  return request<OverviewAnalytics>('/api/v1/analytics/overview');
}

export async function getWardAnalytics(
  wardId: string,
  params?: { date_from?: string; date_to?: string; aggregation?: string }
): Promise<ApiEnvelope<WardAnalytics>> {
  const qs = new URLSearchParams();
  if (params?.date_from) qs.set('date_from', params.date_from);
  if (params?.date_to) qs.set('date_to', params.date_to);
  if (params?.aggregation) qs.set('aggregation', params.aggregation);
  const query = qs.toString() ? `?${qs.toString()}` : '';
  return request<WardAnalytics>(`/api/v1/analytics/ward/${encodeURIComponent(wardId)}${query}`);
}

export { ApiError };
