import React, { useState, useEffect } from 'react';
import {
  fetchWards,
  fetchWardDetail,
  fetchForecast,
  fetchReports,
  submitReport,
  subscribeAlert,
  fetchAlertPreview,
  fetchHealth,
  type WardSummary,
  type WardDetail,
  type Forecast,
  type CitizenReport,
  type AlertPreview,
  type RiskLevel,
  type ReportStatus,
  type Language,
  DEMO_WARDS,
} from './api';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  ReferenceLine,
} from 'recharts';

// ─────────────────────────────────────────────────────────────
// Risk Badge & Color Utilities
// ─────────────────────────────────────────────────────────────
const RISK_COLORS: Record<RiskLevel, { bg: string; text: string; border: string; label: string }> = {
  low: { bg: 'rgba(16, 185, 129, 0.15)', text: '#34d399', border: '#10b981', label: 'Low Risk' },
  moderate: { bg: 'rgba(245, 158, 11, 0.15)', text: '#fbbf24', border: '#f59e0b', label: 'Moderate' },
  high: { bg: 'rgba(249, 115, 22, 0.15)', text: '#fb923c', border: '#f97316', label: 'High Risk' },
  critical: { bg: 'rgba(239, 68, 68, 0.2)', text: '#f87171', border: '#ef4444', label: 'Critical' },
  historical_context: { bg: 'rgba(148, 163, 184, 0.12)', text: '#94a3b8', border: '#64748b', label: 'Historical Record' },
};

export default function App() {
  // Navigation tabs
  const [activeTab, setActiveTab] = useState<'dashboard' | 'analytics' | 'report' | 'alerts' | 'edge' | 'transparency'>('dashboard');

  // Core Data States
  const [wards, setWards] = useState<WardSummary[]>(DEMO_WARDS);
  const [selectedWardId, setSelectedWardId] = useState<string>('dk-kodialbail');
  const [wardDetail, setWardDetail] = useState<WardDetail | null>(null);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [reports, setReports] = useState<CitizenReport[]>([]);
  const [alertPreview, setAlertPreview] = useState<AlertPreview | null>(null);
  const [previewLang, setPreviewLang] = useState<Language>('en-IN');
  const [dataMode, setDataMode] = useState<string>('real');
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(false);
  const [_loading, setLoading] = useState<boolean>(true);
  const [scenarioSelection, setScenarioSelection] = useState<'none' | 'normal' | 'low' | 'dry'>('none');

  // Form states
  const [reportStatus, setReportStatus] = useState<ReportStatus>('dry');
  const [reportTankerBooked, setReportTankerBooked] = useState<boolean>(false);
  const [reportPhone, setReportPhone] = useState<string>('');
  const [reportNote, setReportNote] = useState<string>('');
  const [reportSubmitted, setReportSubmitted] = useState<boolean>(false);
  const [reportSubmitting, setReportSubmitting] = useState<boolean>(false);

  // Alert Subscription state
  const [subPhone, setSubPhone] = useState<string>('');
  const [subLang, setSubLang] = useState<Language>('en-IN');
  const [subSuccess, setSubSuccess] = useState<string | null>(null);

  // Edge Simulation state
  const [edgeSimReadings, setEdgeSimReadings] = useState<Array<{
    timestamp: string;
    ward_id: string;
    depth_m: number;
    voltage: number;
    rssi: number;
  }>>([
    { timestamp: '10:35:12', ward_id: 'dk-kodialbail', depth_m: 13.82, voltage: 3.72, rssi: -62 },
    { timestamp: '10:35:10', ward_id: 'dk-surathkal', depth_m: 14.21, voltage: 3.68, rssi: -71 },
    { timestamp: '10:35:08', ward_id: 'dk-kankanady', depth_m: 12.08, voltage: 3.75, rssi: -58 },
  ]);

  // Initial load
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const health = await fetchHealth().catch(() => null);
        if (health && health.status === 'ok') {
          setIsBackendConnected(true);
          if (health.data_mode) setDataMode(health.data_mode);
        }

        const wardData = await fetchWards().catch(() => null);
        if (wardData && wardData.wards.length > 0) {
          setWards(wardData.wards);
          if (wardData.data_mode) setDataMode(wardData.data_mode);
        }
      } catch (err) {
        console.warn('Backend unavailable, running in local demo mode', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // When selected ward changes, load ward detail, forecast, reports, and alert preview
  useEffect(() => {
    if (!selectedWardId) return;

    let isMounted = true;
    async function loadWardData() {
      try {
        const scenarioParam = scenarioSelection === 'none' ? undefined : scenarioSelection;
        const [detRes, fcRes, repRes, alertRes] = await Promise.allSettled([
          fetchWardDetail(selectedWardId),
          fetchForecast(selectedWardId, scenarioParam),
          fetchReports(selectedWardId),
          fetchAlertPreview(selectedWardId, previewLang),
        ]);

        if (!isMounted) return;

        if (detRes.status === 'fulfilled') {
          setWardDetail(detRes.value.ward);
        }
        if (fcRes.status === 'fulfilled') {
          setForecast(fcRes.value.forecast);
        }
        if (repRes.status === 'fulfilled') {
          setReports(repRes.value.reports);
        }
        if (alertRes.status === 'fulfilled') {
          setAlertPreview(alertRes.value.preview);
        }
      } catch (e) {
        console.error('Error fetching ward data', e);
      }
    }

    loadWardData();
    return () => { isMounted = false; };
  }, [selectedWardId, previewLang, scenarioSelection]);

  // Handle citizen report submit
  const handleReportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setReportSubmitting(true);
    try {
      await submitReport({
        ward_id: selectedWardId,
        status: reportStatus,
        tanker_booked: reportTankerBooked,
        phone: reportPhone ? `+91${reportPhone.replace(/\D/g, '')}` : undefined,
        note: reportNote || undefined,
      });
      setReportSubmitted(true);
      // Reload reports
      const updated = await fetchReports(selectedWardId).catch(() => ({ reports: [] }));
      setReports(updated.reports);
      setTimeout(() => setReportSubmitted(false), 5000);
      setReportNote('');
      setReportPhone('');
    } catch (err) {
      alert(`Submission failed: ${(err as Error).message}`);
    } finally {
      setReportSubmitting(false);
    }
  };

  // Handle alert subscription
  const handleSubscribe = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subPhone) return;
    try {
      await subscribeAlert({
        phone: `+91${subPhone.replace(/\D/g, '')}`,
        language: subLang,
        ward_ids: [selectedWardId],
      });
      setSubSuccess(`Subscribed! DEMO NOTICE: In live mode, alerts send via AWS SNS & Amazon Polly. No real SMS sent.`);
      setSubPhone('');
      setTimeout(() => setSubSuccess(null), 7000);
    } catch (err) {
      alert(`Subscription failed: ${(err as Error).message}`);
    }
  };

  // Simulate incoming edge telemetry tick
  const simulateEdgeTick = () => {
    const curWard = wards.find((w) => w.ward_id === selectedWardId) || wards[0];
    const noise = (Math.random() - 0.5) * 0.1;
    const base = curWard.groundwater_depth_m || 12.0;
    const newReading = {
      timestamp: new Date().toLocaleTimeString(),
      ward_id: curWard.ward_id,
      depth_m: Number((base + noise).toFixed(2)),
      voltage: Number((3.7 + (Math.random() - 0.5) * 0.1).toFixed(2)),
      rssi: Math.floor(-70 + Math.random() * 15),
    };
    setEdgeSimReadings((prev) => [newReading, ...prev.slice(0, 9)]);
  };

  const selectedWard = wards.find((w) => w.ward_id === selectedWardId) || wards[0];
  const activeForecast = forecast || (wardDetail ? wardDetail.forecast : null);
  const isHistoricalOnly = (selectedWard.risk_level === 'historical_context' || activeForecast?.risk_level === 'historical_context' || activeForecast?.forecast_status === 'historical_context_only') && scenarioSelection === 'none';
  const isScenario = Boolean(activeForecast?.is_scenario_simulation || scenarioSelection !== 'none');

  // Prepare chart data
  const forecastChartData = activeForecast && activeForecast.forecast_series
    ? activeForecast.forecast_series.map((item) => ({
        date: item.date.slice(5), // mm-dd
        depth: item.predicted_depth_m,
      }))
    : [
        { date: 'Oct 01', depth: selectedWard.groundwater_depth_m || 12.0 },
        { date: 'Oct 08', depth: (selectedWard.groundwater_depth_m || 12.0) + 0.3 },
        { date: 'Oct 15', depth: (selectedWard.groundwater_depth_m || 12.0) + 0.7 },
        { date: 'Oct 22', depth: (selectedWard.groundwater_depth_m || 12.0) + 1.2 },
        { date: 'Oct 29', depth: (selectedWard.groundwater_depth_m || 12.0) + 1.8 },
      ];

  const rainfallChartData = wardDetail && wardDetail.rainfall_series && wardDetail.rainfall_series.length > 0
    ? wardDetail.rainfall_series.slice(-10).map((r) => ({
        date: r.date.slice(5),
        rainfall: r.rainfall_mm,
      }))
    : [
        { date: '10-01', rainfall: 4.2 },
        { date: '10-02', rainfall: 1.0 },
        { date: '10-03', rainfall: 0.0 },
        { date: '10-04', rainfall: 0.0 },
        { date: '10-05', rainfall: 8.5 },
        { date: '10-06', rainfall: 2.1 },
        { date: '10-07', rainfall: 0.0 },
      ];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* ─────────────────────────────────────────────────────────────
          1. TOP DATA HONESTY & PROVENANCE BANNER
          ───────────────────────────────────────────────────────────── */}
      <aside
        className="demo-banner"
        style={
          dataMode === 'real_historical'
            ? { background: 'rgba(16, 185, 129, 0.15)', borderBottom: '1px solid rgba(16, 185, 129, 0.4)', color: '#34d399' }
            : dataMode === 'hybrid'
            ? { background: 'rgba(6, 182, 212, 0.15)', borderBottom: '1px solid rgba(6, 182, 212, 0.4)', color: '#38bdf8' }
            : { background: 'rgba(245, 158, 11, 0.15)', borderBottom: '1px solid rgba(245, 158, 11, 0.4)', color: '#fbbf24' }
        }
        aria-label="Data mode notice"
      >
        <span style={{ marginRight: '8px' }}>
          {dataMode === 'real_historical' ? '📊' : dataMode === 'hybrid' ? '🔬' : '⚠️'}
        </span>
        {dataMode === 'real_historical' ? (
          <span>
            <strong>Historical CGWB data mode — quarterly observations, not live monitoring.</strong> Edge transducers and SMS broadcasts are simulated.
          </span>
        ) : dataMode === 'hybrid' ? (
          <span>
            <strong>Hybrid mode: groundwater depth is derived from historical CGWB observations; rainfall and ward-level stress estimates include clearly labeled model/demo assumptions.</strong>
          </span>
        ) : (
          <span>
            <strong>Demo mode — sample/synthetic data.</strong> Operating on sample baselines. No real SMS or automated payments are dispatched.
          </span>
        )}
      </aside>

      {/* ─────────────────────────────────────────────────────────────
          2. GLOBAL NAVBAR
          ───────────────────────────────────────────────────────────── */}
      <nav className="nav">
        <div className="container nav-inner">
          <div className="nav-logo">
            <div className="nav-logo-icon">💧</div>
            <div>
              <span style={{ letterSpacing: '-0.02em', fontWeight: 800 }}>JalaNetra</span>
              <span style={{ fontSize: '0.7rem', color: 'var(--color-brand-sky)', marginLeft: '8px', padding: '2px 8px', background: 'rgba(56, 189, 248, 0.1)', borderRadius: '12px', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
                Mangaluru Water Security
              </span>
            </div>
          </div>

          <ul className="nav-links">
            <li>
              <button
                type="button"
                className={activeTab === 'dashboard' ? 'active' : ''}
                onClick={() => setActiveTab('dashboard')}
              >
                Dashboard
              </button>
            </li>
            <li>
              <button
                type="button"
                className={activeTab === 'analytics' ? 'active' : ''}
                onClick={() => setActiveTab('analytics')}
              >
                Depletion Forecast
              </button>
            </li>
            <li>
              <button
                type="button"
                className={activeTab === 'report' ? 'active' : ''}
                onClick={() => setActiveTab('report')}
              >
                Citizen Sahayak
              </button>
            </li>
            <li>
              <button
                type="button"
                className={activeTab === 'alerts' ? 'active' : ''}
                onClick={() => setActiveTab('alerts')}
              >
                Alert Dispatcher
              </button>
            </li>
            <li>
              <button
                type="button"
                className={activeTab === 'edge' ? 'active' : ''}
                onClick={() => setActiveTab('edge')}
              >
                Simulated Edge Feed
              </button>
            </li>
            <li>
              <button
                type="button"
                className={activeTab === 'transparency' ? 'active' : ''}
                onClick={() => setActiveTab('transparency')}
              >
                Data Provenance
              </button>
            </li>
          </ul>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: isBackendConnected ? '#34d399' : '#fbbf24' }}>
              <span
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: isBackendConnected ? '#10b981' : '#f59e0b',
                  display: 'inline-block',
                  boxShadow: isBackendConnected ? '0 0 8px #10b981' : '0 0 8px #f59e0b',
                }}
              />
              <span>{isBackendConnected ? 'FastAPI Live' : 'Demo Local'}</span>
            </div>
          </div>
        </div>
      </nav>

      {/* ─────────────────────────────────────────────────────────────
          3. MAIN CONTAINER
          ───────────────────────────────────────────────────────────── */}
      <main className="container page" style={{ flex: 1 }}>
        {/* Core Promise Hero */}
        <header className="page-hero" style={{ padding: '2rem 0 1.5rem', textAlign: 'left' }}>
          <div style={{ display: 'inline-block', marginBottom: '0.75rem' }}>
            <span className="demo-badge">AWS Environmental Hacks • Heat &amp; Water Track</span>
          </div>
          <h1 style={{ marginBottom: '0.5rem', fontSize: '2.5rem', lineHeight: '1.2' }}>
            India’s rainiest coast is running out of water.
          </h1>
          <p style={{ fontSize: '1.15rem', color: 'var(--color-text-secondary)', maxWidth: '820px' }}>
            <strong>JalaNetra</strong> fuses India WRIS open groundwater baselines, IMD precipitation data,
            crowdsourced citizen reports, and simulated edge well telemetry to tell Mangaluru households
            <strong> exactly which week to act</strong>.
          </p>
        </header>

        {/* ─────────────────────────────────────────────────────────────
            CORE ACTION ALERT BOX (STALE-DATA GUARDRAIL & SCENARIO-AWARE)
            ───────────────────────────────────────────────────────────── */}
        {isHistoricalOnly ? (
          <section
            style={{
              background: 'rgba(30, 41, 59, 0.7)',
              border: '1.5px solid rgba(148, 163, 184, 0.35)',
              borderRadius: 'var(--radius-lg)',
              padding: '1.5rem',
              marginBottom: '1.5rem',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.25)',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div
                  style={{
                    width: '44px',
                    height: '44px',
                    borderRadius: '12px',
                    background: 'linear-gradient(135deg, #475569, #64748b)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1.5rem',
                  }}
                >
                  🏛️
                </div>
                <div>
                  <span style={{ fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase', color: '#94a3b8', letterSpacing: '0.1em' }}>
                    HISTORICAL OBSERVATION • CURRENT FORECAST UNAVAILABLE • WARD: {selectedWard.display_name.toUpperCase()}
                  </span>
                  <h2 style={{ fontSize: '1.35rem', color: '#f1f5f9', margin: '2px 0 0' }}>
                    Historical groundwater context — current forecast unavailable
                  </h2>
                </div>
              </div>

              <div
                style={{
                  background: 'rgba(15, 23, 42, 0.7)',
                  padding: '8px 16px',
                  borderRadius: '12px',
                  border: '1px solid rgba(148, 163, 184, 0.3)',
                  textAlign: 'right',
                }}
              >
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>GOVERNMENT RECORD DATE</div>
                <div style={{ fontSize: '1rem', fontWeight: 600, color: '#94a3b8' }}>
                  {selectedWard.depth_observed_at || 'Quarterly CGWB'}
                  {selectedWard.observation_age_days ? ` (~${Math.round(selectedWard.observation_age_days / 365)}+ yrs ago)` : ''}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', background: 'rgba(6, 15, 30, 0.6)', padding: '12px 16px', borderRadius: '8px' }}>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center' }}>
                <div style={{ flex: 1, minWidth: '220px', fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>
                  <strong>Freshness Disclosure:</strong>{' '}
                  {activeForecast?.explanation || `The latest verified CGWB groundwater observation for this matched station is from ${selectedWard.depth_observed_at || 'past government records'}. It is useful for historical context but too old for a current household water forecast.`}
                  <div style={{ marginTop: '6px', color: '#cbd5e1' }}>
                    <strong>Recommended Next Step:</strong>{' '}
                    {activeForecast?.recommended_action || 'This record is historical. Report today’s water availability or connect a recent ward measurement before making a tanker-booking decision.'}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    className="btn btn-primary btn-sm"
                    onClick={() => setActiveTab('report')}
                  >
                    📢 Report Today’s Water Status
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={() => setScenarioSelection('dry')}
                  >
                    🔬 Test What-if Scenarios
                  </button>
                </div>
              </div>

              <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '8px' }}>
                <strong>Data Provenance &amp; Freshness:</strong>{' '}
                {selectedWard.matched_station ? (
                  <span>
                    CGWB Monitoring Station: <strong style={{ color: 'var(--color-brand-aqua)' }}>{selectedWard.matched_station}</strong> (Depth: {selectedWard.groundwater_depth_m} m bgl observed on {selectedWard.depth_observed_at || 'Quarterly'}).{' '}
                    <em>Historical quarterly government groundwater observations; not live groundwater sensor data.</em>
                  </span>
                ) : (
                  <span style={{ color: '#94a3b8' }}>
                    Historical regional baseline — no live sensor telemetry connected.
                  </span>
                )}
              </div>
            </div>
          </section>
        ) : (
          <section
            style={{
              background: isScenario
                ? 'linear-gradient(135deg, rgba(6, 182, 212, 0.15), rgba(59, 130, 246, 0.12))'
                : 'linear-gradient(135deg, rgba(249, 115, 22, 0.15), rgba(239, 68, 68, 0.12))',
              border: isScenario ? '2px dashed rgba(56, 189, 248, 0.6)' : '2px solid rgba(249, 115, 22, 0.5)',
              borderRadius: 'var(--radius-lg)',
              padding: '1.5rem',
              marginBottom: '1.5rem',
              boxShadow: isScenario ? '0 8px 32px rgba(6, 182, 212, 0.15)' : '0 8px 32px rgba(249, 115, 22, 0.15)',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div
                  style={{
                    width: '44px',
                    height: '44px',
                    borderRadius: '12px',
                    background: isScenario ? 'linear-gradient(135deg, #06b6d4, #3b82f6)' : 'linear-gradient(135deg, #f97316, #ef4444)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1.5rem',
                  }}
                >
                  {isScenario ? '🔬' : '🚨'}
                </div>
                <div>
                  <span style={{ fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase', color: isScenario ? '#38bdf8' : '#fb923c', letterSpacing: '0.1em' }}>
                    {isScenario ? 'WHAT-IF SCENARIO SIMULATION' : 'ACTIONABLE CITIZEN EARLY WARNING'} • WARD: {selectedWard.display_name.toUpperCase()}
                  </span>
                  <h2 style={{ fontSize: '1.4rem', color: '#ffffff', margin: '2px 0 0' }}>
                    {activeForecast && activeForecast.weeks_to_dry !== null
                      ? `Water stress is likely in ${selectedWard.name} in approximately ${activeForecast.weeks_to_dry} ${activeForecast.weeks_to_dry === 1 ? 'week' : 'weeks'}.`
                      : `Water stress advisory for ${selectedWard.name}.`}
                  </h2>
                </div>
              </div>

              {activeForecast?.book_tanker_by && (
                <div
                  style={{
                    background: 'rgba(0,0,0,0.4)',
                    padding: '8px 16px',
                    borderRadius: '12px',
                    border: isScenario ? '1px solid rgba(56, 189, 248, 0.4)' : '1px solid rgba(249, 115, 22, 0.4)',
                    textAlign: 'right',
                  }}
                >
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                    {isScenario ? 'SIMULATED ADVISORY' : 'RECOMMENDED ACTION'}
                  </div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fbbf24' }}>
                    Book tanker by {activeForecast.book_tanker_by}
                  </div>
                </div>
              )}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', background: 'rgba(6, 15, 30, 0.6)', padding: '12px 16px', borderRadius: '8px' }}>
              {isScenario && (
                <div style={{ padding: '6px 10px', borderRadius: '6px', background: 'rgba(56, 189, 248, 0.1)', border: '1px solid rgba(56, 189, 248, 0.3)', color: '#38bdf8', fontSize: '0.85rem' }}>
                  🔬 <strong>Scenario simulation — based on your selected current water report, not a live groundwater reading.</strong>
                </div>
              )}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center' }}>
                <div style={{ flex: 1, minWidth: '220px', fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>
                  <strong>Heuristic Reason:</strong>{' '}
                  {activeForecast ? activeForecast.explanation : `Current well depth is ${selectedWard.groundwater_depth_m}m bgl.`}
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    type="button"
                    className="btn btn-primary btn-sm"
                    onClick={() => setActiveTab('report')}
                  >
                    📢 Report Tap Status
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={() => setActiveTab('alerts')}
                  >
                    📲 SMS Alert Preview
                  </button>
                </div>
              </div>

              <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '8px' }}>
                <strong>Data Provenance &amp; Freshness:</strong>{' '}
                {selectedWard.matched_station ? (
                  <span>
                    CGWB Monitoring Station: <strong style={{ color: 'var(--color-brand-aqua)' }}>{selectedWard.matched_station}</strong> (Observed: {selectedWard.depth_observed_at || 'Quarterly'}).{' '}
                    <em>Historical quarterly government groundwater observations; not live groundwater sensor data.</em>
                  </span>
                ) : (
                  <span style={{ color: '#fbbf24' }}>
                    No direct matched government well observation for this ward; using synthetic seasonal fallback.
                  </span>
                )}
              </div>
            </div>
          </section>
        )}

        {/* ─────────────────────────────────────────────────────────────
            WHAT-IF SCENARIO SIMULATOR (DEMO STORY EXPLORER)
            ───────────────────────────────────────────────────────────── */}
        <section
          style={{
            background: 'rgba(15, 23, 42, 0.75)',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.25rem 1.5rem',
            marginBottom: '2rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <span style={{ fontSize: '0.7rem', fontWeight: 800, textTransform: 'uppercase', color: '#38bdf8', letterSpacing: '0.1em' }}>
                WHAT-IF SCENARIO SIMULATOR • DEMO EXPLORER
              </span>
              <h3 style={{ fontSize: '1.1rem', margin: '2px 0 0', color: '#ffffff' }}>
                Simulate Current Household Water Conditions
              </h3>
              <p style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)', margin: '2px 0 0', maxWidth: '650px' }}>
                Since CGWB observations are historical, choose a hypothetical present-day ground signal to test how JalaNetra forecasts and alerts respond:
              </p>
            </div>

            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <button
                type="button"
                className={`btn btn-sm ${scenarioSelection === 'none' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setScenarioSelection('none')}
              >
                Verified Historical (Default)
              </button>
              <button
                type="button"
                className={`btn btn-sm ${scenarioSelection === 'normal' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setScenarioSelection('normal')}
              >
                💧 Normal supply
              </button>
              <button
                type="button"
                className={`btn btn-sm ${scenarioSelection === 'low' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setScenarioSelection('low')}
              >
                ⚠️ Low supply
              </button>
              <button
                type="button"
                className={`btn btn-sm ${scenarioSelection === 'dry' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setScenarioSelection('dry')}
              >
                🚨 No water (Dry)
              </button>
            </div>
          </div>

          {scenarioSelection !== 'none' && (
            <div style={{ marginTop: '0.75rem', padding: '8px 12px', background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: '8px', fontSize: '0.8rem', color: '#fbbf24' }}>
              🔬 <strong>Scenario simulation — based on your selected current water report, not a live groundwater reading.</strong> Historical CGWB depth and station records remain unperturbed.
            </div>
          )}
        </section>

        {/* ─────────────────────────────────────────────────────────────
            WARD PICKER RIBBON
            ───────────────────────────────────────────────────────────── */}
        <section style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <h3 style={{ fontSize: '1.1rem', color: 'var(--color-text-primary)' }}>Select Mangaluru Ward / Aquifer Zone</h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>Dakshina Kannada Coastal Belt</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            {wards.map((w) => {
              const isSelected = w.ward_id === selectedWardId;
              const rColor = RISK_COLORS[w.risk_level] || RISK_COLORS.low;
              return (
                <div
                  key={w.ward_id}
                  onClick={() => setSelectedWardId(w.ward_id)}
                  className="card card-clickable"
                  style={{
                    padding: '1rem',
                    border: isSelected ? '2px solid var(--color-brand-aqua)' : '1px solid var(--color-border)',
                    background: isSelected ? 'rgba(6, 182, 212, 0.08)' : 'var(--color-surface-card)',
                    position: 'relative',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                    <strong style={{ fontSize: '1rem', color: isSelected ? 'var(--color-brand-aqua)' : 'var(--color-text-primary)' }}>
                      {w.name}
                    </strong>
                    <span
                      style={{
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        padding: '2px 8px',
                        borderRadius: '12px',
                        background: rColor.bg,
                        color: rColor.text,
                        border: `1px solid ${rColor.border}`,
                        textTransform: 'uppercase',
                      }}
                    >
                      {w.risk_level === 'historical_context' ? 'Historical' : w.risk_level}
                    </span>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginTop: '4px' }}>
                    <span>Depth:</span>
                    <strong style={{ color: 'var(--color-text-primary)' }}>{w.groundwater_depth_m} m bgl</strong>
                  </div>

                  {w.depth_observed_at && (
                    <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                      Govt Record: {w.depth_observed_at}
                    </div>
                  )}

                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginTop: '4px' }}>
                    <span>Forecast:</span>
                    <span style={{ color: w.risk_level === 'historical_context' ? '#94a3b8' : (w.days_to_dry_estimate && w.days_to_dry_estimate < 15 ? '#f87171' : 'var(--color-text-primary)') }}>
                      {w.risk_level === 'historical_context' ? 'Historical Context' : (w.days_to_dry_estimate ? `~${w.days_to_dry_estimate} days` : 'Adequate')}
                    </span>
                  </div>

                  {w.book_tanker_by && w.risk_level !== 'historical_context' && (
                    <div style={{ marginTop: '8px', fontSize: '0.75rem', color: '#fbbf24', background: 'rgba(245, 158, 11, 0.1)', padding: '4px 6px', borderRadius: '4px' }}>
                      Tanker by: {w.book_tanker_by}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>

        {/* ─────────────────────────────────────────────────────────────
            TAB CONTENT: DASHBOARD & OVERVIEW
            ───────────────────────────────────────────────────────────── */}
        {activeTab === 'dashboard' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {/* Quick Stats Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
              <div className="card">
                <span className="stat-label">Well Groundwater Depth</span>
                <div className="stat-value" style={{ color: 'var(--color-brand-sky)' }}>
                  {selectedWard.groundwater_depth_m} <span style={{ fontSize: '1rem' }}>m bgl</span>
                </div>
                <span className="stat-sub">Depth below ground level</span>
              </div>

              <div className="card">
                <span className="stat-label">7-Day Local Rainfall</span>
                <div className="stat-value" style={{ color: 'var(--color-brand-teal)' }}>
                  {selectedWard.rainfall_7d_mm || 12.8} <span style={{ fontSize: '1rem' }}>mm</span>
                </div>
                <span className="stat-sub">IMD Station / Synthetic gauge</span>
              </div>

              <div className="card">
                <span className="stat-label">Aquifer Stress Level</span>
                <div className="stat-value" style={{ color: RISK_COLORS[selectedWard.risk_level]?.text }}>
                  {selectedWard.risk_level.toUpperCase()}
                </div>
                <span className="stat-sub">Confidence: {selectedWard.confidence}</span>
              </div>

              <div className="card">
                <span className="stat-label">Estimated Days to Dry</span>
                <div className="stat-value" style={{ color: '#fb923c' }}>
                  {selectedWard.days_to_dry_estimate ? `${selectedWard.days_to_dry_estimate} d` : 'Stable'}
                </div>
                <span className="stat-sub">{selectedWard.book_tanker_by ? `Book: ${selectedWard.book_tanker_by}` : 'No immediate tanker needed'}</span>
              </div>
            </div>

            {/* Interactive Charts Section */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '1.5rem' }}>
              {/* Depletion Curve Chart */}
              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <div>
                    <h3 style={{ fontSize: '1.1rem' }}>Groundwater Level &amp; Forecast</h3>
                    <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                      Depth in metres below ground level (higher = lower water table)
                    </p>
                  </div>
                  <span className="demo-badge">Forecast Model</span>
                </div>

                <div style={{ height: '240px', width: '100%' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={forecastChartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                      <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
                      <YAxis stroke="#64748b" domain={['dataMin - 1', 'dataMax + 2']} fontSize={12} />
                      <Tooltip
                        contentStyle={{ background: '#0f2444', borderColor: '#38bdf8', borderRadius: '8px', color: '#f0f9ff' }}
                        formatter={(val: any) => [`${Number(val).toFixed(2)} m bgl`, 'Water Depth']}
                      />
                      <ReferenceLine y={16} label={{ value: 'Configurable demo stress threshold (16m bgl)', fill: '#ef4444', fontSize: 10 }} stroke="#ef4444" strokeDasharray="4 4" />
                      <Line type="monotone" dataKey="depth" stroke="#38bdf8" strokeWidth={3} dot={{ r: 4, fill: '#06b6d4' }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Rainfall Chart */}
              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <div>
                    <h3 style={{ fontSize: '1.1rem' }}>Precipitation History</h3>
                    <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                      Precipitation (mm) over observation cycle
                    </p>
                  </div>
                  <span className="demo-badge">IMD / Sample</span>
                </div>

                <div style={{ height: '240px', width: '100%' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={rainfallChartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                      <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
                      <YAxis stroke="#64748b" fontSize={12} />
                      <Tooltip
                        contentStyle={{ background: '#0f2444', borderColor: '#0d9488', borderRadius: '8px', color: '#f0f9ff' }}
                        formatter={(val: any) => [`${val} mm`, 'Rainfall']}
                      />
                      <Bar dataKey="rainfall" fill="#0d9488" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* Quick Action Cards Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
              <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <h4 style={{ color: 'var(--color-brand-sky)', marginBottom: '8px' }}>📢 Citizen Ground Feedback</h4>
                  <p style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>
                    Are your taps running dry today in {selectedWard.name}? Crowdsourced reports calibrate municipal tanker routes.
                  </p>
                </div>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => setActiveTab('report')}
                >
                  Submit 1-Click Tap Status
                </button>
              </div>

              <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <h4 style={{ color: '#fbbf24', marginBottom: '8px' }}>📲 Simulated Alert Dispatcher</h4>
                  <p style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>
                    Preview multilingual SMS and synthesized Polly voice dispatches sent to registered residents.
                  </p>
                </div>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setActiveTab('alerts')}
                >
                  Inspect SMS &amp; Voice Broadcasts
                </button>
              </div>

              <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <h4 style={{ color: '#34d399', marginBottom: '8px' }}>📡 AWS IoT Greengrass Node Roadmap</h4>
                  <p style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>
                    Simulated edge telemetry for a future optional AWS IoT Greengrass sensor-node roadmap. No physical edge device was used in this demo.
                  </p>
                </div>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setActiveTab('edge')}
                >
                  Open Edge Telemetry Feed
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ─────────────────────────────────────────────────────────────
            TAB CONTENT: DEPLETION FORECAST DEEP-DIVE
            ───────────────────────────────────────────────────────────── */}
        {activeTab === 'analytics' && (
          <div className="card" style={{ padding: '2rem' }}>
            <div className="section-header">
              <div className="section-eyebrow">AQUIFER MODEL EXPLANATION</div>
              <h2>Depletion Trajectory &amp; Rule-Based Forecast</h2>
              <p>
                Mangaluru’s lateritic aquifer responds sharply to the cessation of the South-West monsoon.
                JalaNetra’s transparent heuristic models depletion rate based on depth headroom, post-monsoon draw,
                and precipitation recharge.
              </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
              <div style={{ background: 'var(--color-surface-2)', padding: '1.25rem', borderRadius: '12px' }}>
                <span className="stat-label">Model Architecture</span>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--color-brand-sky)', margin: '4px 0' }}>
                  Deterministic Coastal Aquifer Heuristic
                </div>
                <p style={{ fontSize: '0.85rem' }}>
                  No unexplainable black-box ML. Clear, auditable rules based on CGWB geological benchmarks for coastal Karnataka.
                </p>
              </div>

              <div style={{ background: 'var(--color-surface-2)', padding: '1.25rem', borderRadius: '12px' }}>
                <span className="stat-label">Depletion Rate</span>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fb923c', margin: '4px 0' }}>
                  {activeForecast && activeForecast.depth_trend_m_per_month !== null
                    ? `${activeForecast.depth_trend_m_per_month > 0 ? '+' : ''}${activeForecast.depth_trend_m_per_month} m / month`
                    : '+0.50 m / month (Seasonal dry estimate)'}
                </div>
                <p style={{ fontSize: '0.85rem' }}>
                  Reflects seasonal recharge slowing down and domestic borewell extraction.
                </p>
              </div>

              <div style={{ background: 'var(--color-surface-2)', padding: '1.25rem', borderRadius: '12px' }}>
                <span className="stat-label">Confidence Score</span>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#34d399', margin: '4px 0' }}>
                  {selectedWard.confidence.toUpperCase()}
                </div>
                <p style={{ fontSize: '0.85rem' }}>
                  Automatically downgraded to &lsquo;low&rsquo; when operating on sparse or synthetic sample records.
                </p>
              </div>
            </div>

            <div style={{ background: 'rgba(6, 15, 30, 0.7)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--color-border)' }}>
              <h4 style={{ color: 'var(--color-brand-aqua)', marginBottom: '8px' }}>Official Forecast Summary</h4>
              <p style={{ fontSize: '1rem', color: 'var(--color-text-primary)', marginBottom: '1rem' }}>
                {activeForecast?.explanation || 'Ward groundwater levels are entering critical dry-season trajectory.'}
              </p>
              <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '10px' }}>
                <strong>Recommended Action:</strong> {activeForecast?.recommended_action || 'Prepare tanker backup schedule.'}
              </div>
            </div>
          </div>
        )}

        {/* ─────────────────────────────────────────────────────────────
            TAB CONTENT: CITIZEN REPORTING ("JALANETRA SAHAYAK")
            ───────────────────────────────────────────────────────────── */}
        {activeTab === 'report' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '2rem' }}>
            <div className="card">
              <div className="section-header" style={{ marginBottom: '1.5rem' }}>
                <div className="section-eyebrow">CITIZEN CROWDSOURCING</div>
                <h3>Submit Water Supply Status</h3>
                <p style={{ fontSize: '0.85rem' }}>
                  Citizen ground reports directly influence JalaNetra’s ward stress rating. A single verified dry report elevates risk.
                </p>
              </div>

              {reportSubmitted && (
                <div className="alert-box success" style={{ marginBottom: '1rem' }}>
                  <span>✓</span>
                  <div>
                    <strong>Report Recorded!</strong> Thank you for updating ground truth for {selectedWard.name}.
                    Phone masked for privacy.
                  </div>
                </div>
              )}

              <form onSubmit={handleReportSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <div className="form-group">
                  <label className="form-label">Ward</label>
                  <select
                    className="form-select"
                    value={selectedWardId}
                    onChange={(e) => setSelectedWardId(e.target.value)}
                  >
                    {wards.map((w) => (
                      <option key={w.ward_id} value={w.ward_id}>
                        {w.display_name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Tap Status Today</label>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
                    <button
                      type="button"
                      className={`btn btn-sm ${reportStatus === 'came' ? 'btn-primary' : 'btn-secondary'}`}
                      onClick={() => setReportStatus('came')}
                      style={{ justifyContent: 'center' }}
                    >
                      💧 Normal Flow
                    </button>
                    <button
                      type="button"
                      className={`btn btn-sm ${reportStatus === 'low' ? 'btn-primary' : 'btn-secondary'}`}
                      onClick={() => setReportStatus('low')}
                      style={{ justifyContent: 'center' }}
                    >
                      ⚠️ Low Pressure
                    </button>
                    <button
                      type="button"
                      className={`btn btn-sm ${reportStatus === 'dry' ? 'btn-danger' : 'btn-secondary'}`}
                      onClick={() => setReportStatus('dry')}
                      style={{ justifyContent: 'center' }}
                    >
                      ❌ Dry / No Water
                    </button>
                  </div>
                </div>

                <div className="form-group">
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={reportTankerBooked}
                      onChange={(e) => setReportTankerBooked(e.target.checked)}
                      style={{ width: '18px', height: '18px', accentColor: 'var(--color-brand-teal)' }}
                    />
                    <span style={{ fontSize: '0.9rem' }}>I already ordered a private water tanker today</span>
                  </label>
                </div>

                <div className="form-group">
                  <label className="form-label">Phone Number (Optional - Masked &amp; Private)</label>
                  <input
                    type="tel"
                    className="form-input"
                    placeholder="9876543210"
                    value={reportPhone}
                    onChange={(e) => setReportPhone(e.target.value)}
                    maxLength={10}
                  />
                  <span className="form-hint">Stored strictly as masked token (e.g. +91 98*** **210). Never shared.</span>
                </div>

                <div className="form-group">
                  <label className="form-label">Additional Observations (Optional)</label>
                  <textarea
                    className="form-textarea"
                    rows={2}
                    placeholder="e.g. Well pump sucking air since 6 AM; tanker arrived after 4 hours delay."
                    value={reportNote}
                    onChange={(e) => setReportNote(e.target.value)}
                  />
                </div>

                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={reportSubmitting}
                >
                  {reportSubmitting ? 'Recording...' : 'Submit Citizen Report'}
                </button>
              </form>
            </div>

            {/* Recent Reports in this ward */}
            <div className="card">
              <div className="section-header" style={{ marginBottom: '1rem' }}>
                <div className="section-eyebrow">COMMUNITY PULSE</div>
                <h3>Recent Reports in {selectedWard.name}</h3>
                <p style={{ fontSize: '0.85rem' }}>Live ground feed recorded in local database.</p>
              </div>

              {reports.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-text-muted)' }}>
                  No citizen reports submitted for this ward yet today. Be the first to report!
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '420px', overflowY: 'auto' }}>
                  {reports.map((r, i) => (
                    <div
                      key={r.id || i}
                      style={{
                        background: 'var(--color-surface-2)',
                        padding: '12px',
                        borderRadius: '8px',
                        borderLeft: `4px solid ${r.status === 'dry' ? '#ef4444' : r.status === 'low' ? '#f59e0b' : '#10b981'}`,
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 700, textTransform: 'uppercase', fontSize: '0.8rem', color: r.status === 'dry' ? '#f87171' : r.status === 'low' ? '#fbbf24' : '#34d399' }}>
                          Status: {r.status === 'dry' ? 'No Supply (Dry)' : r.status === 'low' ? 'Low Pressure' : 'Normal Flow'}
                        </span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                          {r.created_at ? new Date(r.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Recent'}
                        </span>
                      </div>
                      {r.tanker_booked && (
                        <div style={{ fontSize: '0.75rem', color: '#fb923c', marginTop: '4px' }}>
                          🚚 Private tanker booked
                        </div>
                      )}
                      {r.note && (
                        <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginTop: '4px' }}>
                          &ldquo;{r.note}&rdquo;
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ─────────────────────────────────────────────────────────────
            TAB CONTENT: ALERT DISPATCHER (SIMULATED AWS SNS & POLLY)
            ───────────────────────────────────────────────────────────── */}
        {activeTab === 'alerts' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '2rem' }}>
            {/* Live Alert Preview Card */}
            <div className="card">
              <div className="section-header" style={{ marginBottom: '1rem' }}>
                <div className="section-eyebrow">AWS SNS &amp; AMAZON POLLY PREVIEW</div>
                <h3>Illustrative Alert Scenario Preview</h3>
                <div style={{ margin: '8px 0 12px', padding: '8px 12px', background: 'rgba(56, 189, 248, 0.1)', border: '1px solid rgba(56, 189, 248, 0.25)', borderRadius: '8px', fontSize: '0.8rem', color: '#38bdf8' }}>
                  ℹ️ <strong>Illustrative scenario preview — not triggered by current measurements.</strong>
                </div>
                <p style={{ fontSize: '0.85rem' }}>
                  Inspect the automated SMS and synthesized voice notification scripts configured for Amazon Polly and AWS SNS.
                </p>
              </div>

              <div style={{ display: 'flex', gap: '8px', marginBottom: '1.25rem' }}>
                <button
                  type="button"
                  className={`btn btn-sm ${previewLang === 'en-IN' ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => setPreviewLang('en-IN')}
                >
                  English (en-IN)
                </button>
                <button
                  type="button"
                  className={`btn btn-sm ${previewLang === 'hi-IN' ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => setPreviewLang('hi-IN')}
                >
                  Hindi / हिन्दी (hi-IN)
                </button>
              </div>

              {/* SMS Bubble */}
              <div style={{ marginBottom: '1.5rem' }}>
                <span className="stat-label">📱 SMS Message Payload</span>
                <div
                  style={{
                    background: '#07182e',
                    border: '1px solid rgba(56, 189, 248, 0.3)',
                    borderRadius: '12px',
                    padding: '1rem',
                    fontFamily: 'monospace',
                    fontSize: '0.9rem',
                    color: '#e0f2fe',
                    lineHeight: '1.5',
                    marginTop: '6px',
                  }}
                >
                  {previewLang === 'en-IN'
                    ? (alertPreview?.sms_text_en || `[SCENARIO PREVIEW] JalaNetra: Illustrative preview for ${selectedWard.name}. Historical CGWB observation only — current forecast unavailable. Report status at jalanetra.demo`)
                    : (alertPreview?.sms_text_hi || `[परिदृश्य पूर्वावलोकन] JalaNetra: ${selectedWard.name} के लिए सांकेतिक पूर्वावलोकन। केवल ऐतिहासिक CGWB डेटा — वर्तमान पूर्वानुमान अनुपलब्ध। jalanetra.demo पर स्थिति दर्ज करें`)}
                </div>
              </div>

              {/* Voice Script Bubble */}
              <div>
                <span className="stat-label">🎙️ Amazon Polly-Compatible Voice-Alert Script Preview</span>
                <div
                  style={{
                    background: 'rgba(13, 148, 136, 0.08)',
                    border: '1px solid rgba(13, 148, 136, 0.3)',
                    borderRadius: '12px',
                    padding: '1rem',
                    fontSize: '0.9rem',
                    color: '#99f6e4',
                    lineHeight: '1.6',
                    marginTop: '6px',
                  }}
                >
                  {previewLang === 'en-IN'
                    ? (alertPreview?.voice_text_en || `Hello. This is an illustrative scenario preview for JalaNetra. For ${selectedWard.name}, verified CGWB groundwater data is historical and current forecast is unavailable. Please report your tap status at jalanetra.demo. Thank you.`)
                    : (alertPreview?.voice_text_hi || `नमस्ते। यह JalaNetra की ओर से एक सांकेतिक परिदृश्य पूर्वावलोकन है। ${selectedWard.name} के लिए उपलब्ध भूजल डेटा ऐतिहासिक है और वर्तमान पूर्वानुमान अनुपलब्ध है। धन्यवाद।`)}
                </div>
              </div>

              <div style={{ marginTop: '1.5rem', padding: '10px', background: 'rgba(245, 158, 11, 0.1)', borderRadius: '8px', border: '1px solid rgba(245, 158, 11, 0.3)', fontSize: '0.8rem', color: '#fbbf24' }}>
                🔒 <strong>Demo Safety Guarantee:</strong> Illustrative scenario preview only. No real cellular broadcasts are dispatched.
              </div>
            </div>

            {/* Subscribe Form */}
            <div className="card">
              <div className="section-header" style={{ marginBottom: '1.5rem' }}>
                <div className="section-eyebrow">HOUSEHOLD ENROLLMENT</div>
                <h3>Subscribe for Alerts (Demo)</h3>
                <p style={{ fontSize: '0.85rem' }}>
                  Register your ward to receive water stress forecasts. Masked and sanitized locally.
                </p>
              </div>

              {subSuccess && (
                <div className="alert-box success" style={{ marginBottom: '1.25rem' }}>
                  <span>✓</span>
                  <div>{subSuccess}</div>
                </div>
              )}

              <form onSubmit={handleSubscribe} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <div className="form-group">
                  <label className="form-label">Phone Number (10 digits)</label>
                  <input
                    type="tel"
                    className="form-input"
                    placeholder="9876543210"
                    required
                    value={subPhone}
                    onChange={(e) => setSubPhone(e.target.value)}
                    maxLength={10}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Alert Language</label>
                  <select
                    className="form-select"
                    value={subLang}
                    onChange={(e) => setSubLang(e.target.value as Language)}
                  >
                    <option value="en-IN">English (en-IN)</option>
                    <option value="hi-IN">Hindi / हिन्दी (hi-IN)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Target Ward</label>
                  <select
                    className="form-select"
                    value={selectedWardId}
                    onChange={(e) => setSelectedWardId(e.target.value)}
                  >
                    {wards.map((w) => (
                      <option key={w.ward_id} value={w.ward_id}>
                        {w.display_name}
                      </option>
                    ))}
                  </select>
                </div>

                <button type="submit" className="btn btn-primary">
                  Enroll Phone for Alerts (Demo Mode)
                </button>
              </form>
            </div>
          </div>
        )}

        {/* ─────────────────────────────────────────────────────────────
            TAB CONTENT: SIMULATED EDGE SENSOR FEED
            ───────────────────────────────────────────────────────────── */}
        {activeTab === 'edge' && (
          <div className="card" style={{ padding: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
              <div>
                <div className="section-eyebrow">EDGE SENSOR SIMULATOR</div>
                <h2>Simulated AWS IoT Greengrass Telemetry</h2>
                <p style={{ maxWidth: '680px' }}>
                  Simulated edge telemetry for a future optional AWS IoT Greengrass sensor-node roadmap. No physical edge device was used in this demo.
                </p>
              </div>
              <button
                type="button"
                className="btn btn-primary"
                onClick={simulateEdgeTick}
              >
                ⚡ Trigger Edge Reading
              </button>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-text-muted)' }}>
                    <th style={{ padding: '10px' }}>TIMESTAMP</th>
                    <th style={{ padding: '10px' }}>DEVICE ID</th>
                    <th style={{ padding: '10px' }}>WARD</th>
                    <th style={{ padding: '10px' }}>DEPTH (m bgl)</th>
                    <th style={{ padding: '10px' }}>BATTERY</th>
                    <th style={{ padding: '10px' }}>RSSI</th>
                    <th style={{ padding: '10px' }}>STATUS</th>
                  </tr>
                </thead>
                <tbody>
                  {edgeSimReadings.map((r, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                      <td style={{ padding: '10px', fontFamily: 'monospace' }}>{r.timestamp}</td>
                      <td style={{ padding: '10px', fontFamily: 'monospace', color: 'var(--color-brand-sky)' }}>
                        greengrass-{r.ward_id}
                      </td>
                      <td style={{ padding: '10px', fontWeight: 600 }}>{r.ward_id}</td>
                      <td style={{ padding: '10px', fontWeight: 700, color: '#fb923c' }}>{r.depth_m} m</td>
                      <td style={{ padding: '10px' }}>{r.voltage} V</td>
                      <td style={{ padding: '10px' }}>{r.rssi} dBm</td>
                      <td style={{ padding: '10px' }}>
                        <span className="demo-badge" style={{ fontSize: '0.65rem' }}>SIMULATED</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ─────────────────────────────────────────────────────────────
            TAB CONTENT: DATA PROVENANCE & TRANSPARENCY
            ───────────────────────────────────────────────────────────── */}
        {activeTab === 'transparency' && (
          <div className="card" style={{ padding: '2rem' }}>
            <div className="section-header">
              <div className="section-eyebrow">AUDITABILITY &amp; DATA HONESTY</div>
              <h2>Data Provenance &amp; Environmental Integrity</h2>
              <p>
                In strict adherence to the hackathon guidelines, JalaNetra never misrepresents simulated data as live observations.
              </p>
            </div>

            <div
              style={{
                marginBottom: '1.5rem',
                padding: '1rem 1.25rem',
                borderRadius: '12px',
                background: 'rgba(6, 182, 212, 0.12)',
                border: '1px solid rgba(6, 182, 212, 0.35)',
                color: '#38bdf8',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
              }}
            >
              <span style={{ fontSize: '1.4rem' }}>🔬</span>
              <div>
                <strong>Hybrid mode: groundwater depth is derived from historical CGWB observations; rainfall and ward-level stress estimates include clearly labeled model/demo assumptions.</strong>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
              <div style={{ background: 'var(--color-surface-2)', padding: '1.25rem', borderRadius: '12px' }}>
                <h4 style={{ color: 'var(--color-brand-teal)', marginBottom: '6px' }}>1. India WRIS / CGWB Groundwater</h4>
                <p style={{ fontSize: '0.85rem' }}>
                  Ingested 4,962 historical observations across 115 monitoring stations in Dakshina Kannada (1996–2020) from <code>gwl_manual_quarterly_cgwb_ka_1991_2020.csv</code>.
                  <br /><strong style={{ color: '#34d399' }}>Quarterly government observations; not live groundwater sensor data.</strong>
                </p>
              </div>

              <div style={{ background: 'var(--color-surface-2)', padding: '1.25rem', borderRadius: '12px' }}>
                <h4 style={{ color: 'var(--color-brand-sky)', marginBottom: '6px' }}>2. IMD Rainfall Records</h4>
                <p style={{ fontSize: '0.85rem' }}>
                  Precipitation baselines calibrated against historical coastal Karnataka monsoon averages (~3,800 mm annual rainfall).
                </p>
              </div>

              <div style={{ background: 'var(--color-surface-2)', padding: '1.25rem', borderRadius: '12px' }}>
                <h4 style={{ color: '#fbbf24', marginBottom: '6px' }}>3. Citizen Ground Truth</h4>
                <p style={{ fontSize: '0.85rem' }}>
                  Hyper-local household verification of tap flow and private tanker dispatches stored locally with phone hashing.
                </p>
              </div>

              <div style={{ background: 'var(--color-surface-2)', padding: '1.25rem', borderRadius: '12px' }}>
                <h4 style={{ color: '#f87171', marginBottom: '6px' }}>4. Simulated Edge Nodes</h4>
                <p style={{ fontSize: '0.85rem' }}>
                  Microcontroller/Jetson ultrasonic sensors simulated via Python mock publisher with synthetic flags on every JSON payload.
                </p>
              </div>
            </div>

            <div style={{ background: 'rgba(6, 15, 30, 0.7)', padding: '1.25rem', borderRadius: '12px', border: '1px solid var(--color-border)' }}>
              <h4 style={{ marginBottom: '8px' }}>AWS Cloud Infrastructure Architecture</h4>
              <p style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>
                Infrastructure as Code defined under <code>infra/app.py</code> using AWS CDK v2:
                Amazon API Gateway, AWS Lambda (Python 3.11), Amazon DynamoDB (Single-table design),
                Amazon SNS (SMS dispatch), Amazon Polly (Multilingual voice synthesis), and AWS IoT Greengrass v2.
              </p>
            </div>
          </div>
        )}
      </main>

      {/* ─────────────────────────────────────────────────────────────
          GLOBAL FOOTER
          ───────────────────────────────────────────────────────────── */}
      <footer className="footer">
        <div className="container">
          <p>
            <strong>JalaNetra</strong> — Mangaluru Water Security Early Warning System.
            Built for WeMakeDevs x AWS Environmental Hacks (Heat &amp; Water Track).
          </p>
          <p style={{ fontSize: '0.75rem', marginTop: '6px', color: 'var(--color-text-muted)' }}>
            DEMO MODE • All simulated telemetry clearly marked. Never exposes credentials or sends unrequested communications.
          </p>
        </div>
      </footer>
    </div>
  );
}
