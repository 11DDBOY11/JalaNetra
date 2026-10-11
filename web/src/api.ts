// JalaNetra API client and types

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

// ────────────────────────────────────────────
// Types
// ────────────────────────────────────────────

export type RiskLevel = 'low' | 'moderate' | 'high' | 'critical' | 'historical_context';
export type Confidence = 'low' | 'medium' | 'high';
export type ReportStatus = 'came' | 'low' | 'dry';
export type Language = 'en-IN' | 'hi-IN';

export interface WardSummary {
  ward_id: string;
  name: string;
  display_name: string;
  latitude: number;
  longitude: number;
  groundwater_depth_m: number | null;
  depth_observed_at: string | null;
  rainfall_7d_mm: number | null;
  risk_level: RiskLevel;
  forecast_status?: 'current_active' | 'historical_context_only' | 'scenario_simulation';
  forecast_current?: boolean;
  observation_age_days?: number | null;
  days_to_dry_estimate: number | null;
  weeks_to_dry?: number | null;
  book_tanker_by: string | null;
  confidence: Confidence;
  recommended_action?: string;
  explanation?: string;
  synthetic: boolean;
  groundwater_synthetic?: boolean;
  matched_station?: string | null;
  freshness_disclosure?: string;
  data_mode: string;
}

export interface ForecastSeries {
  date: string;
  predicted_depth_m: number;
  synthetic: boolean;
}

export interface GroundwaterPoint {
  date: string;
  depth_m: number;
  synthetic: boolean;
}

export interface RainfallPoint {
  date: string;
  rainfall_mm: number;
  synthetic: boolean;
}

export interface Forecast {
  ward_id: string;
  ward_name: string;
  risk_level: RiskLevel;
  forecast_status?: 'current_active' | 'historical_context_only' | 'scenario_simulation';
  forecast_current?: boolean;
  observation_age_days?: number | null;
  days_to_dry_estimate: number | null;
  weeks_to_dry: number | null;
  book_tanker_by: string | null;
  confidence: Confidence;
  explanation: string;
  recommended_action: string;
  groundwater_depth_m: number;
  depth_trend_m_per_month: number | null;
  rainfall_7d_mm: number;
  forecast_series: ForecastSeries[];
  model: string;
  data_mode: string;
  synthetic: boolean;
  computed_at: string;
  citizen_dry_report: boolean;
  is_scenario_simulation?: boolean;
  scenario_selected?: string;
  scenario_label?: string;
}

export interface WardDetail {
  ward_id: string;
  name: string;
  display_name: string;
  latitude: number;
  longitude: number;
  groundwater_depth_m: number | null;
  depth_observed_at: string | null;
  depth_trend_m_per_month: number | null;
  rainfall_rainfall_7d_mm: number | null;
  rainfall_rainfall_30d_mm: number | null;
  synthetic: boolean;
  data_mode: string;
  last_updated: string;
  groundwater_series: GroundwaterPoint[];
  rainfall_series: RainfallPoint[];
  forecast: Forecast;
  recent_reports_count: number;
}

export interface CitizenReport {
  id: number;
  ward_id: string;
  status: ReportStatus;
  tanker_booked: boolean;
  created_at: string;
  note?: string;
}

export interface AlertPreview {
  demo_only: boolean;
  no_sms_sent: boolean;
  alert_triggered: boolean;
  trigger_reason: string;
  ward_id: string;
  ward_name: string;
  risk_level: RiskLevel;
  book_tanker_by: string | null;
  sms_text_en: string;
  sms_text_hi: string;
  voice_text_en: string;
  voice_text_hi: string;
  aws_polly_voice_en: string;
  aws_polly_voice_hi: string;
  disclaimer: string;
  data_mode: string;
  synthetic: boolean;
}

export interface ApiResponse<T = unknown> {
  data_mode: string;
  synthetic: boolean;
  groundwater_source_mode?: string;
  rainfall_source_mode?: string;
  ward_estimate_mode?: string;
  generated_at: string;
  data?: T;
  [key: string]: unknown;
}

// ────────────────────────────────────────────
// Demo fallback data (used when backend unavailable)
// ────────────────────────────────────────────

const addDays = (days: number) => {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().split('T')[0];
};

export const DEMO_FALLBACK_WARDS: WardSummary[] = [
  {
    ward_id: 'dk-kodialbail',
    name: 'Kodialbail',
    display_name: 'Kodialbail Ward',
    latitude: 12.87,
    longitude: 74.88,
    groundwater_depth_m: 9.8,
    depth_observed_at: '2026-10-01',
    rainfall_7d_mm: 12.8,
    risk_level: 'moderate',
    days_to_dry_estimate: 28,
    book_tanker_by: addDays(21),
    confidence: 'low',
    synthetic: true,
    data_mode: 'demo',
  },
  {
    ward_id: 'dk-kankanady',
    name: 'Kankanady',
    display_name: 'Kankanady Ward',
    latitude: 12.91,
    longitude: 74.86,
    groundwater_depth_m: 12.1,
    depth_observed_at: '2026-10-01',
    rainfall_7d_mm: 12.8,
    risk_level: 'high',
    days_to_dry_estimate: 14,
    book_tanker_by: addDays(7),
    confidence: 'low',
    synthetic: true,
    data_mode: 'demo',
  },
  {
    ward_id: 'dk-kadri',
    name: 'Kadri',
    display_name: 'Kadri Ward',
    latitude: 12.88,
    longitude: 74.85,
    groundwater_depth_m: 8.3,
    depth_observed_at: '2026-10-01',
    rainfall_7d_mm: 12.8,
    risk_level: 'low',
    days_to_dry_estimate: 60,
    book_tanker_by: null,
    confidence: 'low',
    synthetic: true,
    data_mode: 'demo',
  },
  {
    ward_id: 'dk-surathkal',
    name: 'Surathkal',
    display_name: 'Surathkal Ward',
    latitude: 13.0,
    longitude: 74.79,
    groundwater_depth_m: 14.2,
    depth_observed_at: '2026-10-01',
    rainfall_7d_mm: 12.8,
    risk_level: 'critical',
    days_to_dry_estimate: 5,
    book_tanker_by: addDays(2),
    confidence: 'low',
    synthetic: true,
    data_mode: 'demo',
  },
  {
    ward_id: 'dk-moodbidri',
    name: 'Moodbidri',
    display_name: 'Moodbidri Ward',
    latitude: 12.96,
    longitude: 74.99,
    groundwater_depth_m: 11.4,
    depth_observed_at: '2026-10-01',
    rainfall_7d_mm: 12.8,
    risk_level: 'moderate',
    days_to_dry_estimate: 21,
    book_tanker_by: addDays(14),
    confidence: 'low',
    synthetic: true,
    data_mode: 'demo',
  },
];

export const DEMO_WARDS = DEMO_FALLBACK_WARDS;

// ────────────────────────────────────────────
// API fetch wrapper
// ────────────────────────────────────────────

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(err.detail || err.error || `HTTP ${response.status}`);
  }
  return response.json();
}

// ────────────────────────────────────────────
// API functions
// ────────────────────────────────────────────

export async function fetchWards(): Promise<{ wards: WardSummary[]; data_mode: string; synthetic: boolean }> {
  return apiFetch('/api/wards');
}

export async function fetchWardDetail(wardId: string): Promise<{ ward: WardDetail; data_mode: string; synthetic: boolean }> {
  return apiFetch(`/api/wards/${wardId}`);
}

export async function fetchForecast(wardId: string, scenario?: string): Promise<{ forecast: Forecast; data_mode: string; synthetic: boolean }> {
  const url = scenario ? `/api/forecast?ward_id=${wardId}&scenario=${encodeURIComponent(scenario)}` : `/api/forecast?ward_id=${wardId}`;
  return apiFetch(url);
}

export async function fetchReports(wardId: string): Promise<{ reports: CitizenReport[] }> {
  return apiFetch(`/api/reports?ward_id=${wardId}`);
}

export async function submitReport(data: {
  ward_id: string;
  status: ReportStatus;
  tanker_booked: boolean;
  phone?: string;
  note?: string;
}): Promise<{ ok: boolean; report_id: number }> {
  return apiFetch('/api/reports', { method: 'POST', body: JSON.stringify(data) });
}

export async function subscribeAlert(data: {
  phone: string;
  language: Language;
  ward_ids: string[];
}): Promise<{ ok: boolean; no_sms_will_be_sent: boolean }> {
  return apiFetch('/api/alerts/subscribe', { method: 'POST', body: JSON.stringify(data) });
}

export async function fetchAlertPreview(wardId: string, language: Language): Promise<{ preview: AlertPreview; data_mode: string }> {
  return apiFetch('/api/alerts/preview', {
    method: 'POST',
    body: JSON.stringify({ ward_id: wardId, language }),
  });
}

export async function fetchHealth(): Promise<{ status: string; data_mode: string }> {
  return apiFetch('/health');
}
