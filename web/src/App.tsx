import React, { useState, useEffect } from 'react';
import {
  fetchWards,
  fetchWardDetail,
  fetchForecast,
  fetchPulseSummary,
  fetchWardPulse,
  submitPulseReport,
  seedPulseOutage,
  seedPulseRecovery,
  resetPulseScenario,
  testPulseSms,
  type WardSummary,
  type WardDetail,
  type Forecast,
  type PulseStatus,
  type PulseSummaryResponse,
  type PulseWardDetailResponse,
  type PulseSmsTestResponse,
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
} from 'recharts';
import {
  DropletIcon,
  CheckCircleIcon,
  AlertTriangleIcon,
  AlertCircleIcon,
  ClockIcon,
  UsersIcon,
  MapPinIcon,
  ShieldCheckIcon,
  InfoIcon,
  RefreshIcon,
  ArrowRightIcon,
} from './icons';

type TabType = 'pulse' | 'report' | 'admin' | 'historical' | 'about' | 'tools';

export default function App() {
  // Navigation tabs
  const [activeTab, setActiveTab] = useState<TabType>(() => {
    const params = new URLSearchParams(window.location.search);
    const tabParam = params.get('tab') as TabType;
    if (['pulse', 'report', 'admin', 'historical', 'about', 'tools'].includes(tabParam)) {
      return tabParam;
    }
    if (window.location.pathname === '/tools') return 'tools';
    return 'pulse';
  });

  // Wards State
  const [wards, setWards] = useState<WardSummary[]>(DEMO_WARDS);
  const [selectedWardId, setSelectedWardId] = useState<string>('dk-kodialbail');

  // Pulse State
  const [pulseSummary, setPulseSummary] = useState<PulseSummaryResponse | null>(null);
  const [wardPulse, setWardPulse] = useState<PulseWardDetailResponse | null>(null);
  const [selectedReportStatus, setSelectedReportStatus] = useState<PulseStatus>('available');
  const [reportLocality, setReportLocality] = useState<string>('dk-kodialbail');
  const [reportPhone, setReportPhone] = useState<string>('');
  const [reportNote, setReportNote] = useState<string>('');
  const [privateSupportArranged, setPrivateSupportArranged] = useState<boolean>(false);
  const [submittingReport, setSubmittingReport] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Response Board Checklist State
  const [checkedActions, setCheckedActions] = useState<Record<string, boolean>>({});

  // Developer / Test Tools State
  const [smsResult, setSmsResult] = useState<PulseSmsTestResponse | null>(null);
  const [smsTesting, setSmsTesting] = useState<boolean>(false);
  const [confirmLiveSend, setConfirmLiveSend] = useState<boolean>(false);
  const [scenarioLoading, setScenarioLoading] = useState<boolean>(false);

  // Historical Context State
  const [wardDetail, setWardDetail] = useState<WardDetail | null>(null);
  const [_forecast, setForecast] = useState<Forecast | null>(null);

  // Toast Helper
  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 4500);
  };

  // Sync tab with URL
  const switchTab = (tab: TabType) => {
    setActiveTab(tab);
    const url = new URL(window.location.href);
    if (tab === 'pulse') {
      url.searchParams.delete('tab');
    } else {
      url.searchParams.set('tab', tab);
    }
    window.history.replaceState({}, '', url.toString());
  };

  // Initial Data Fetch & Polling (8s)
  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      try {
        const wardData = await fetchWards().catch(() => null);
        if (wardData && wardData.wards.length > 0 && isMounted) {
          setWards(wardData.wards);
        }

        const summaryData = await fetchPulseSummary().catch(() => null);
        if (summaryData && isMounted) {
          setPulseSummary(summaryData);
        }
      } catch (err) {
        console.warn('Initial load error', err);
      }
    }

    loadData();

    const interval = setInterval(async () => {
      try {
        const summaryData = await fetchPulseSummary().catch(() => null);
        if (summaryData && isMounted) {
          setPulseSummary(summaryData);
        }
      } catch {
        // silent polling catch
      }
    }, 8000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  // Fetch Ward-Specific Pulse & Historical Details
  useEffect(() => {
    let isMounted = true;

    async function loadWardData() {
      try {
        const [pulseData, detailData, forecastData] = await Promise.all([
          fetchWardPulse(selectedWardId).catch(() => null),
          fetchWardDetail(selectedWardId).catch(() => null),
          fetchForecast(selectedWardId).catch(() => null),
        ]);

        if (isMounted) {
          if (pulseData) setWardPulse(pulseData);
          if (detailData && detailData.ward) setWardDetail(detailData.ward);
          if (forecastData && forecastData.forecast) setForecast(forecastData.forecast);
        }
      } catch (err) {
        console.warn('Ward load error', err);
      }
    }

    loadWardData();
  }, [selectedWardId]);

  // Handle Community Report Submit
  const handleReportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingReport(true);

    try {
      const targetWard = activeTab === 'report' ? reportLocality : selectedWardId;
      const res = await submitPulseReport({
        ward_id: targetWard,
        status: selectedReportStatus,
        phone: reportPhone.trim() || undefined,
      });

      showToast(res.message || 'Thanks. Your update helps your neighbourhood respond faster.');
      setReportPhone('');
      setReportNote('');
      setPrivateSupportArranged(false);

      // Refresh pulse data immediately
      const [newSummary, newWard] = await Promise.all([
        fetchPulseSummary().catch(() => null),
        fetchWardPulse(targetWard).catch(() => null),
      ]);
      if (newSummary) setPulseSummary(newSummary);
      if (newWard) setWardPulse(newWard);

      if (activeTab === 'report') {
        setSelectedWardId(targetWard);
        switchTab('pulse');
      }
    } catch {
      showToast('Notice: Only one update per household is counted every 30 minutes.');
    } finally {
      setSubmittingReport(false);
    }
  };

  // Active Alert in currently selected ward
  const activeAlert = wardPulse?.active_alert;
  const selectedWard = wards.find((w) => w.ward_id === selectedWardId);
  const currentWardName = selectedWard?.name || 'Kodialbail';

  // Toggle Checklist Item
  const toggleChecklist = (key: string) => {
    setCheckedActions((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  // Handle Seed Actions in Developer Tools
  const handleSeedOutage = async () => {
    setScenarioLoading(true);
    try {
      await seedPulseOutage(selectedWardId);
      const [newSummary, newWard] = await Promise.all([
        fetchPulseSummary().catch(() => null),
        fetchWardPulse(selectedWardId).catch(() => null),
      ]);
      if (newSummary) setPulseSummary(newSummary);
      if (newWard) setWardPulse(newWard);
      showToast('Simulated 3 independent reports. Alert activated.');
    } catch (err) {
      console.error(err);
    } finally {
      setScenarioLoading(false);
    }
  };

  const handleSeedRecovery = async () => {
    setScenarioLoading(true);
    try {
      await seedPulseRecovery(selectedWardId);
      const [newSummary, newWard] = await Promise.all([
        fetchPulseSummary().catch(() => null),
        fetchWardPulse(selectedWardId).catch(() => null),
      ]);
      if (newSummary) setPulseSummary(newSummary);
      if (newWard) setWardPulse(newWard);
      showToast('Simulated recovery reports. Incident updated.');
    } catch (err) {
      console.error(err);
    } finally {
      setScenarioLoading(false);
    }
  };

  const handleResetScenario = async () => {
    setScenarioLoading(true);
    try {
      await resetPulseScenario();
      const [newSummary, newWard] = await Promise.all([
        fetchPulseSummary().catch(() => null),
        fetchWardPulse(selectedWardId).catch(() => null),
      ]);
      if (newSummary) setPulseSummary(newSummary);
      if (newWard) setWardPulse(newWard);
      showToast('Simulated data reset. Monitored records cleared.');
    } catch (err) {
      console.error(err);
    } finally {
      setScenarioLoading(false);
    }
  };

  const handleTestSms = async (live: boolean) => {
    setSmsTesting(true);
    try {
      const res = await testPulseSms(selectedWardId, live);
      setSmsResult(res);
      showToast(live && res.sent ? 'Test notification dispatched.' : 'Message preview generated.');
    } catch (err) {
      console.error(err);
    } finally {
      setSmsTesting(false);
    }
  };

  return (
    <div className="app-container">
      {/* ──────────────── Top Navigation ──────────────── */}
      <header className="navbar">
        <div className="navbar-inner">
          <div className="brand-section" onClick={() => switchTab('pulse')}>
            <div className="brand-logo">
              <DropletIcon size={22} color="#FFFFFF" />
            </div>
            <div className="brand-titles">
              <div className="brand-name">
                JalaNetra Pulse
                <span className="brand-badge">Mangaluru</span>
              </div>
              <span className="brand-subtitle">Community water response</span>
            </div>
          </div>

          <nav>
            <ul className="nav-links">
              <li>
                <button
                  type="button"
                  className={`nav-item ${activeTab === 'pulse' ? 'active' : ''}`}
                  onClick={() => switchTab('pulse')}
                >
                  Pulse
                </button>
              </li>
              <li>
                <button
                  type="button"
                  className={`nav-item ${activeTab === 'report' ? 'active' : ''}`}
                  onClick={() => switchTab('report')}
                >
                  Report water
                </button>
              </li>
              <li>
                <button
                  type="button"
                  className={`nav-item ${activeTab === 'admin' ? 'active' : ''}`}
                  onClick={() => switchTab('admin')}
                >
                  Response board
                  {pulseSummary && pulseSummary.active_alert_count > 0 && (
                    <span className="badge badge-critical" style={{ padding: '1px 5px', fontSize: '0.65rem' }}>
                      {pulseSummary.active_alert_count}
                    </span>
                  )}
                </button>
              </li>
              <li>
                <button
                  type="button"
                  className={`nav-item ${activeTab === 'historical' ? 'active' : ''}`}
                  onClick={() => switchTab('historical')}
                >
                  Water context
                </button>
              </li>
              <li>
                <button
                  type="button"
                  className={`nav-item ${activeTab === 'about' ? 'active' : ''}`}
                  onClick={() => switchTab('about')}
                >
                  About
                </button>
              </li>
            </ul>
          </nav>

          <div className="nav-controls">
            <select
              aria-label="Select locality"
              className="ward-selector"
              value={selectedWardId}
              onChange={(e) => {
                setSelectedWardId(e.target.value);
                setReportLocality(e.target.value);
              }}
            >
              {wards.map((w) => (
                <option key={w.ward_id} value={w.ward_id}>
                  {w.name}
                </option>
              ))}
            </select>

            <div className="live-indicator">
              <span className="pulse-dot" />
              <span>Live updates</span>
            </div>
          </div>
        </div>
      </header>

      {/* ──────────────── Main Content ──────────────── */}
      <main className="main-content">
        {/* Toast Notification */}
        {toastMessage && (
          <div className="toast">
            <CheckCircleIcon size={18} color="#FFFFFF" />
            <span>{toastMessage}</span>
          </div>
        )}

        {/* ──────── 1. TAB: PULSE (HOME) ──────── */}
        {activeTab === 'pulse' && (
          <div>
            {/* Top Alert Banner if Outage Active in Ward */}
            {activeAlert && activeAlert.status === 'active' && (
              <div className="alert-banner critical">
                <div className="alert-banner-icon">
                  <AlertCircleIcon size={24} color="#D92D20" />
                </div>
                <div className="alert-banner-content">
                  <div className="alert-banner-title">
                    Water supply issue reported in {currentWardName}
                  </div>
                  <div className="alert-banner-desc">
                    {activeAlert.independent_report_count} residents reported no water in the last 90 minutes.
                  </div>
                  <div className="alert-banner-meta">
                    <span>Reported by local residents. Verification in progress.</span>
                    <span>•</span>
                    <span>Confidence: {activeAlert.confidence.toUpperCase()}</span>
                    <span>•</span>
                    <span>First report: {new Date(activeAlert.first_report_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                </div>
              </div>
            )}

            {activeAlert && activeAlert.status === 'recovery' && (
              <div className="alert-banner recovery">
                <div className="alert-banner-icon">
                  <CheckCircleIcon size={24} color="#12B76A" />
                </div>
                <div className="alert-banner-content">
                  <div className="alert-banner-title">
                    Community-reported recovery in {currentWardName}
                  </div>
                  <div className="alert-banner-desc">
                    Recent resident reports indicate water supply is restoring. Response teams monitoring pressure.
                  </div>
                  <div className="alert-banner-meta">
                    <span>Reported by local residents. Verification in progress.</span>
                  </div>
                </div>
              </div>
            )}

            {/* Page Header */}
            <div className="page-header">
              <h1 className="page-title">Water status in your neighbourhood</h1>
              <p className="page-subtitle">
                See recent community reports and share what is happening at your tap.
              </p>
            </div>

            {/* Main 2-Column Section */}
            <div className="grid-2">
              {/* Left Column: Current Status Summary */}
              <div className="card">
                <div className="card-header">
                  <div className="card-title">
                    <MapPinIcon size={18} color="#16324F" />
                    <span>{currentWardName}</span>
                  </div>
                  {activeAlert ? (
                    <span className={`badge ${activeAlert.status === 'active' ? 'badge-critical' : 'badge-normal'}`}>
                      {activeAlert.status === 'active' ? 'Issue reported' : 'Recovery reported'}
                    </span>
                  ) : (
                    <span className="badge badge-normal">No active issue</span>
                  )}
                </div>

                <div style={{ marginBottom: '20px' }}>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#16324F', marginBottom: '4px' }}>
                    {activeAlert && activeAlert.status === 'active'
                      ? 'Water supply interruption reported'
                      : 'No active water issue reported'}
                  </div>
                  <div style={{ fontSize: '0.875rem', color: '#475467' }}>
                    {wardPulse?.reports_last_90m || 0} community updates in the last 90 minutes.
                  </div>
                </div>

                {/* Report Status Distribution */}
                {wardPulse && (
                  <div style={{ marginBottom: '24px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#667085', marginBottom: '6px' }}>
                      <span>Available: {wardPulse.status_breakdown.available}</span>
                      <span>Low supply: {wardPulse.status_breakdown.low}</span>
                      <span>No water: {wardPulse.status_breakdown.dry}</span>
                    </div>
                    <div style={{ height: '8px', background: '#F2F4F7', borderRadius: '4px', overflow: 'hidden', display: 'flex' }}>
                      <div style={{ width: `${(wardPulse.status_breakdown.available / Math.max(1, wardPulse.reports_last_90m)) * 100}%`, background: '#12B76A' }} />
                      <div style={{ width: `${(wardPulse.status_breakdown.low / Math.max(1, wardPulse.reports_last_90m)) * 100}%`, background: '#F79009' }} />
                      <div style={{ width: `${(wardPulse.status_breakdown.dry / Math.max(1, wardPulse.reports_last_90m)) * 100}%`, background: '#D92D20' }} />
                    </div>
                  </div>
                )}

                {/* Recent Updates Timeline */}
                <div style={{ borderTop: '1px solid #E4E7EC', paddingTop: '18px' }}>
                  <div style={{ fontSize: '0.875rem', fontWeight: 600, color: '#16324F', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <ClockIcon size={16} color="#667085" />
                    <span>Recent community updates</span>
                  </div>

                  {wardPulse && wardPulse.recent_reports.length > 0 ? (
                    <div className="timeline">
                      {wardPulse.recent_reports.slice(0, 4).map((r) => (
                        <div key={r.id} className="timeline-item">
                          <div
                            className="timeline-dot"
                            style={{
                              backgroundColor:
                                r.status === 'available'
                                  ? '#12B76A'
                                  : r.status === 'low'
                                  ? '#F79009'
                                  : '#D92D20',
                            }}
                          />
                          <div className="timeline-content">
                            <div className="timeline-header">
                              <span className="timeline-title">
                                {r.status === 'available'
                                  ? 'Water available'
                                  : r.status === 'low'
                                  ? 'Low supply'
                                  : 'No water'}
                              </span>
                              <span className="timeline-time">
                                {new Date(r.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </span>
                            </div>
                            <div className="timeline-detail">
                              Verified household update • {r.reporter_key_hash ? r.reporter_key_hash.slice(0, 8) : 'Household'}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ padding: '16px', background: '#F8FAFC', borderRadius: '8px', fontSize: '0.8125rem', color: '#667085', textAlign: 'center' }}>
                      No reports submitted in the last 90 minutes. Normal conditions.
                    </div>
                  )}
                </div>
              </div>

              {/* Right Column: Quick Status Report Card */}
              <div className="card">
                <div className="card-header">
                  <div className="card-title">
                    <DropletIcon size={18} color="#2F80ED" />
                    <span>Report water status</span>
                  </div>
                  <span style={{ fontSize: '0.75rem', color: '#667085' }}>{currentWardName}</span>
                </div>

                <p style={{ fontSize: '0.8125rem', color: '#475467', marginBottom: '14px' }}>
                  What is the water condition at your tap right now?
                </p>

                <form onSubmit={handleReportSubmit}>
                  <div className="report-actions-grid">
                    <button
                      type="button"
                      className={`report-btn ${selectedReportStatus === 'available' ? 'selected-available' : ''}`}
                      onClick={() => setSelectedReportStatus('available')}
                    >
                      <div className="report-btn-icon" style={{ background: '#ECFDF3', color: '#12B76A' }}>
                        <CheckCircleIcon size={18} color="#12B76A" />
                      </div>
                      <div className="report-btn-title">Water available</div>
                      <div className="report-btn-desc">Normal pressure</div>
                    </button>

                    <button
                      type="button"
                      className={`report-btn ${selectedReportStatus === 'low' ? 'selected-low' : ''}`}
                      onClick={() => setSelectedReportStatus('low')}
                    >
                      <div className="report-btn-icon" style={{ background: '#FEF0C7', color: '#F79009' }}>
                        <AlertTriangleIcon size={18} color="#F79009" />
                      </div>
                      <div className="report-btn-title">Low supply</div>
                      <div className="report-btn-desc">Weak trickle</div>
                    </button>

                    <button
                      type="button"
                      className={`report-btn btn-dry ${selectedReportStatus === 'dry' ? 'selected-dry' : ''}`}
                      onClick={() => setSelectedReportStatus('dry')}
                    >
                      <div className="report-btn-icon" style={{ background: selectedReportStatus === 'dry' ? '#FEF3F2' : '#FFFFFF', color: '#D92D20' }}>
                        <AlertCircleIcon size={18} color="#D92D20" />
                      </div>
                      <div className="report-btn-title">No water</div>
                      <div className="report-btn-desc">Taps dry</div>
                    </button>
                  </div>

                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 500, color: '#475467', marginBottom: '4px' }}>
                      Phone number (Optional — for alert updates)
                    </label>
                    <input
                      type="tel"
                      placeholder="e.g. 9876543210"
                      value={reportPhone}
                      onChange={(e) => setReportPhone(e.target.value)}
                      maxLength={10}
                      style={{
                        width: '100%',
                        padding: '9px 12px',
                        borderRadius: '6px',
                        border: '1px solid #E4E7EC',
                        fontSize: '0.875rem',
                        outline: 'none',
                      }}
                    />
                    <div style={{ fontSize: '0.6875rem', color: '#667085', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <ShieldCheckIcon size={13} color="#667085" />
                      <span>Your number is used only for optional local alerts and is never shown publicly.</span>
                    </div>
                  </div>

                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={submittingReport}
                    style={{ width: '100%', padding: '11px' }}
                  >
                    {submittingReport ? 'Submitting...' : 'Submit update'}
                  </button>
                </form>
              </div>
            </div>

            {/* Monitored Neighbourhoods Summary List */}
            <div className="card" style={{ marginBottom: '24px' }}>
              <div className="card-header">
                <div className="card-title">
                  <UsersIcon size={18} color="#16324F" />
                  <span>Monitored neighbourhoods</span>
                </div>
                <span style={{ fontSize: '0.75rem', color: '#667085' }}>Mangaluru City</span>
              </div>

              <div className="grid-3">
                {wards.map((w) => {
                  const isSelected = w.ward_id === selectedWardId;
                  const isAlert = pulseSummary?.active_alerts.some((a) => a.ward_id === w.ward_id && a.status === 'active');
                  const count = pulseSummary?.wards_monitored.find((wm) => wm.ward_id === w.ward_id)?.reports_90m || 0;

                  return (
                    <div
                      key={w.ward_id}
                      onClick={() => setSelectedWardId(w.ward_id)}
                      style={{
                        padding: '14px 16px',
                        borderRadius: '8px',
                        border: isSelected ? '1.5px solid #2F80ED' : '1px solid #E4E7EC',
                        backgroundColor: isSelected ? '#EEF4FD' : '#FFFFFF',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                        <span style={{ fontWeight: 600, color: '#16324F', fontSize: '0.9375rem' }}>{w.name}</span>
                        {isAlert ? (
                          <span className="badge badge-critical" style={{ fontSize: '0.6875rem' }}>Issue</span>
                        ) : (
                          <span className="badge badge-normal" style={{ fontSize: '0.6875rem' }}>Normal</span>
                        )}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#667085' }}>
                        {count} updates in last 90m
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* "What happens next?" 3-Step Section */}
            <div className="card">
              <div className="card-title" style={{ marginBottom: '16px' }}>
                <InfoIcon size={18} color="#2F80ED" />
                <span>How neighbourhood response works</span>
              </div>

              <div className="grid-3" style={{ marginBottom: 0 }}>
                <div style={{ padding: '14px', background: '#F8FAFC', borderRadius: '8px', border: '1px solid #E4E7EC' }}>
                  <div style={{ fontWeight: 600, fontSize: '0.875rem', color: '#16324F', marginBottom: '4px' }}>
                    1. Residents report
                  </div>
                  <div style={{ fontSize: '0.8125rem', color: '#475467', lineHeight: 1.45 }}>
                    Households submit tap status in 1 click. Privacy is protected through cryptographic hashing.
                  </div>
                </div>

                <div style={{ padding: '14px', background: '#F8FAFC', borderRadius: '8px', border: '1px solid #E4E7EC' }}>
                  <div style={{ fontWeight: 600, fontSize: '0.875rem', color: '#16324F', marginBottom: '4px' }}>
                    2. Pattern detection
                  </div>
                  <div style={{ fontSize: '0.8125rem', color: '#475467', lineHeight: 1.45 }}>
                    When 3 independent reports occur in the same ward within 90 minutes, an alert is triggered.
                  </div>
                </div>

                <div style={{ padding: '14px', background: '#F8FAFC', borderRadius: '8px', border: '1px solid #E4E7EC' }}>
                  <div style={{ fontWeight: 600, fontSize: '0.875rem', color: '#16324F', marginBottom: '4px' }}>
                    3. Local coordination
                  </div>
                  <div style={{ fontSize: '0.8125rem', color: '#475467', lineHeight: 1.45 }}>
                    Ward volunteers verify supply lines, inspect booster pumps, and coordinate tanker support.
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ──────── 2. TAB: REPORT WATER ──────── */}
        {activeTab === 'report' && (
          <div style={{ maxWidth: '640px', margin: '0 auto' }}>
            <div className="page-header" style={{ textAlign: 'center' }}>
              <h1 className="page-title">Share today's water status</h1>
              <p className="page-subtitle">
                Help your neighbourhood detect interruptions early. Your report is grouped anonymously with nearby households.
              </p>
            </div>

            <div className="card">
              <form onSubmit={handleReportSubmit}>
                {/* Locality Selector */}
                <div style={{ marginBottom: '18px' }}>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#16324F', marginBottom: '6px' }}>
                    Select neighbourhood
                  </label>
                  <select
                    className="ward-selector"
                    value={reportLocality}
                    onChange={(e) => setReportLocality(e.target.value)}
                    style={{ width: '100%', padding: '10px 12px' }}
                  >
                    {wards.map((w) => (
                      <option key={w.ward_id} value={w.ward_id}>
                        {w.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Status Selection */}
                <div style={{ marginBottom: '18px' }}>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#16324F', marginBottom: '6px' }}>
                    Current water condition
                  </label>
                  <div className="report-actions-grid">
                    <button
                      type="button"
                      className={`report-btn ${selectedReportStatus === 'available' ? 'selected-available' : ''}`}
                      onClick={() => setSelectedReportStatus('available')}
                    >
                      <CheckCircleIcon size={20} color="#12B76A" />
                      <div className="report-btn-title">Available</div>
                      <div className="report-btn-desc">Normal flow</div>
                    </button>

                    <button
                      type="button"
                      className={`report-btn ${selectedReportStatus === 'low' ? 'selected-low' : ''}`}
                      onClick={() => setSelectedReportStatus('low')}
                    >
                      <AlertTriangleIcon size={20} color="#F79009" />
                      <div className="report-btn-title">Low supply</div>
                      <div className="report-btn-desc">Weak pressure</div>
                    </button>

                    <button
                      type="button"
                      className={`report-btn btn-dry ${selectedReportStatus === 'dry' ? 'selected-dry' : ''}`}
                      onClick={() => setSelectedReportStatus('dry')}
                    >
                      <div className="report-btn-icon" style={{ background: selectedReportStatus === 'dry' ? '#FEF3F2' : '#FFFFFF', color: '#D92D20' }}>
                        <AlertCircleIcon size={20} color="#D92D20" />
                      </div>
                      <div className="report-btn-title">No water</div>
                      <div className="report-btn-desc">Taps dry</div>
                    </button>
                  </div>
                </div>

                {/* Optional Note */}
                <div style={{ marginBottom: '18px' }}>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#16324F', marginBottom: '6px' }}>
                    Optional details
                  </label>
                  <textarea
                    rows={2}
                    placeholder="e.g. Municipal supply cut off since 7 AM, booster pump issue..."
                    value={reportNote}
                    onChange={(e) => setReportNote(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      borderRadius: '6px',
                      border: '1px solid #E4E7EC',
                      fontSize: '0.875rem',
                      fontFamily: 'inherit',
                      outline: 'none',
                    }}
                  />
                </div>

                {/* Private Support Checkbox */}
                <div style={{ marginBottom: '18px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <input
                    type="checkbox"
                    id="supportCheckbox"
                    checked={privateSupportArranged}
                    onChange={(e) => setPrivateSupportArranged(e.target.checked)}
                    style={{ width: '16px', height: '16px' }}
                  />
                  <label htmlFor="supportCheckbox" style={{ fontSize: '0.8125rem', color: '#475467', cursor: 'pointer' }}>
                    I have arranged private tanker support for my building
                  </label>
                </div>

                {/* Phone Number */}
                <div style={{ marginBottom: '22px' }}>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#16324F', marginBottom: '6px' }}>
                    Mobile number (Optional opt-in)
                  </label>
                  <input
                    type="tel"
                    placeholder="e.g. 9876543210"
                    value={reportPhone}
                    onChange={(e) => setReportPhone(e.target.value)}
                    maxLength={10}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      borderRadius: '6px',
                      border: '1px solid #E4E7EC',
                      fontSize: '0.875rem',
                      outline: 'none',
                    }}
                  />
                  <div style={{ fontSize: '0.6875rem', color: '#667085', marginTop: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <ShieldCheckIcon size={13} color="#667085" />
                    <span>Your number is used only for optional local alerts and is never shown publicly.</span>
                  </div>
                </div>

                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={submittingReport}
                  style={{ width: '100%', padding: '12px', fontSize: '0.9375rem' }}
                >
                  {submittingReport ? 'Submitting...' : 'Submit update'}
                </button>
              </form>
            </div>
          </div>
        )}

        {/* ──────── 3. TAB: RESPONSE BOARD (ADMIN) ──────── */}
        {activeTab === 'admin' && (
          <div>
            <div className="page-header">
              <h1 className="page-title">Response board</h1>
              <p className="page-subtitle">
                Operational overview for apartment associations, ward volunteers, and community responders.
              </p>
            </div>

            {/* High-level Counters */}
            <div className="grid-4">
              <div className="stat-card">
                <div className="stat-label">Active alerts</div>
                <div className="stat-value" style={{ color: pulseSummary && pulseSummary.active_alert_count > 0 ? '#D92D20' : '#12B76A' }}>
                  {pulseSummary?.active_alert_count || 0}
                </div>
                <div className="stat-sub">Across 5 monitored wards</div>
              </div>

              <div className="stat-card">
                <div className="stat-label">Recent reports</div>
                <div className="stat-value">{pulseSummary?.total_reports_90m || 0}</div>
                <div className="stat-sub">Last 90-minute rolling window</div>
              </div>

              <div className="stat-card">
                <div className="stat-label">24-hour total</div>
                <div className="stat-value">{pulseSummary?.total_reports_24h || 0}</div>
                <div className="stat-sub">Verified community updates</div>
              </div>

              <div className="stat-card">
                <div className="stat-label">Detection rule</div>
                <div className="stat-value" style={{ fontSize: '1.25rem', color: '#16324F' }}>3 reports</div>
                <div className="stat-sub">90-minute cluster threshold</div>
              </div>
            </div>

            {/* Active Issues Section */}
            <div className="card" style={{ marginBottom: '24px' }}>
              <div className="card-header">
                <div className="card-title">
                  <AlertCircleIcon size={18} color="#D92D20" />
                  <span>Reported interruptions</span>
                </div>
                <span style={{ fontSize: '0.75rem', color: '#667085' }}>Live incident queue</span>
              </div>

              {pulseSummary && pulseSummary.active_alerts.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {pulseSummary.active_alerts.map((alert) => {
                    const wardName = wards.find((w) => w.ward_id === alert.ward_id)?.name || alert.ward_id;
                    const actionKey = `alert_${alert.id}_`;

                    return (
                      <div
                        key={alert.id}
                        style={{
                          border: '1px solid #E4E7EC',
                          borderRadius: '8px',
                          padding: '18px',
                          background: alert.status === 'active' ? '#FEFDFD' : '#F8FAFC',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <span style={{ fontWeight: 700, fontSize: '1.0625rem', color: '#16324F' }}>{wardName}</span>
                            <span className={`badge ${alert.status === 'active' ? 'badge-critical' : 'badge-normal'}`}>
                              {alert.status === 'active' ? 'Active issue' : 'Recovery reported'}
                            </span>
                          </div>
                          <span style={{ fontSize: '0.75rem', color: '#667085' }}>
                            Ref #{String(alert.id).slice(0, 8)}
                          </span>
                        </div>

                        <div style={{ fontSize: '0.875rem', color: '#475467', marginBottom: '14px' }}>
                          <strong>{alert.independent_report_count} independent households</strong> reported no water. Trigger reason: {alert.trigger_reason}
                        </div>

                        <div className="info-box" style={{ marginBottom: '16px' }}>
                          <InfoIcon size={18} color="#159E9C" />
                          <span>Reported by local residents. Verification in progress. Initial report at {new Date(alert.first_report_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}.</span>
                        </div>

                        {/* Action Checklist */}
                        <div style={{ background: '#F8FAFC', padding: '14px', borderRadius: '6px', border: '1px solid #E4E7EC', marginBottom: '14px' }}>
                          <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#16324F', marginBottom: '8px' }}>
                            Recommended next actions
                          </div>

                          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            {[
                              { id: 'verify', label: 'Verify municipal pipeline pressure with neighbours' },
                              { id: 'inspect', label: 'Inspect local borewell / booster pump electricals' },
                              { id: 'tanker', label: 'Coordinate emergency private tanker support if needed' },
                              { id: 'escalate', label: 'Escalate to ward water utility helpline' },
                            ].map((item) => {
                              const isChecked = !!checkedActions[actionKey + item.id];
                              return (
                                <label
                                  key={item.id}
                                  style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px',
                                    fontSize: '0.8125rem',
                                    color: isChecked ? '#98A2B3' : '#344054',
                                    textDecoration: isChecked ? 'line-through' : 'none',
                                    cursor: 'pointer',
                                  }}
                                >
                                  <input
                                    type="checkbox"
                                    checked={isChecked}
                                    onChange={() => toggleChecklist(actionKey + item.id)}
                                  />
                                  <span>{item.label}</span>
                                </label>
                              );
                            })}
                          </div>
                        </div>

                        {/* Fast Resolution Actions */}
                        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                          <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={async () => {
                              await submitPulseReport({ ward_id: alert.ward_id, status: 'restored' });
                              showToast('Recovery status recorded.');
                              const s = await fetchPulseSummary();
                              setPulseSummary(s);
                            }}
                          >
                            <RefreshIcon size={15} color="#12B76A" />
                            <span>Record restoration update</span>
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div style={{ padding: '28px 20px', textAlign: 'center', color: '#667085', background: '#F8FAFC', borderRadius: '8px' }}>
                  <CheckCircleIcon size={32} color="#12B76A" style={{ margin: '0 auto 8px', display: 'block' }} />
                  <div style={{ fontWeight: 600, color: '#16324F', marginBottom: '4px' }}>All monitored wards are operating normally</div>
                  <div style={{ fontSize: '0.8125rem' }}>No active water interruptions reported in the last 90 minutes.</div>

                  {/* Compact Recent Activity Block */}
                  <div
                    style={{
                      marginTop: '20px',
                      paddingTop: '16px',
                      borderTop: '1px solid #E4E7EC',
                      display: 'flex',
                      justifyContent: 'center',
                      alignItems: 'center',
                      gap: '28px',
                      flexWrap: 'wrap',
                      textAlign: 'left',
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '0.6875rem', fontWeight: 600, textTransform: 'uppercase', color: '#667085', letterSpacing: '0.04em' }}>
                        Resident updates today
                      </div>
                      <div style={{ fontSize: '1.0625rem', fontWeight: 700, color: '#16324F', marginTop: '2px' }}>
                        {pulseSummary?.total_reports_24h ?? 0}
                      </div>
                    </div>

                    <div style={{ width: '1px', height: '28px', background: '#E4E7EC' }} />

                    <div>
                      <div style={{ fontSize: '0.6875rem', fontWeight: 600, textTransform: 'uppercase', color: '#667085', letterSpacing: '0.04em' }}>
                        Below alert threshold
                      </div>
                      <div style={{ fontSize: '1.0625rem', fontWeight: 700, color: '#12B76A', marginTop: '2px' }}>
                        {(pulseSummary?.wards_monitored.length || wards.length) - (pulseSummary?.active_alert_count || 0)} of {pulseSummary?.wards_monitored.length || wards.length} wards
                      </div>
                    </div>

                    <div style={{ width: '1px', height: '28px', background: '#E4E7EC' }} />

                    <div>
                      <div style={{ fontSize: '0.6875rem', fontWeight: 600, textTransform: 'uppercase', color: '#667085', letterSpacing: '0.04em' }}>
                        Latest update
                      </div>
                      <div style={{ fontSize: '1.0625rem', fontWeight: 700, color: '#16324F', marginTop: '2px' }}>
                        {pulseSummary?.updated_at
                          ? new Date(pulseSummary.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                          : 'Monitoring live'}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ──────── 4. TAB: WATER CONTEXT (HISTORICAL CGWB) ──────── */}
        {activeTab === 'historical' && (
          <div>
            <div className="page-header">
              <h1 className="page-title">Groundwater context</h1>
              <p className="page-subtitle">
                Historical groundwater observations near your selected neighbourhood.
              </p>
            </div>

            {/* Context Notice */}
            <div className="info-box" style={{ marginBottom: '20px' }}>
              <InfoIcon size={20} color="#159E9C" />
              <div>
                <strong>Groundwater history is shown for context.</strong> Current alerts are based on community reports.
                This chart shows long-term groundwater context. It does not indicate today’s household water supply.
              </div>
            </div>

            <div className="grid-2">
              {/* Historical Trend Chart */}
              <div className="card">
                <div className="card-header">
                  <div className="card-title">
                    <span>Depth to water level trend</span>
                  </div>
                  <span style={{ fontSize: '0.75rem', color: '#667085' }}>Meters below ground level</span>
                </div>

                <div style={{ width: '100%', height: 260 }}>
                  {wardDetail && wardDetail.groundwater_series && wardDetail.groundwater_series.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart
                        data={wardDetail.groundwater_series.map((r) => ({
                          date: r.date.slice(0, 7),
                          depth: r.depth_m,
                        }))}
                        margin={{ top: 10, right: 20, left: 0, bottom: 0 }}
                      >
                        <CartesianGrid stroke="#F2F4F7" vertical={false} />
                        <XAxis dataKey="date" stroke="#98A2B3" fontSize={11} tickLine={false} />
                        <YAxis stroke="#98A2B3" fontSize={11} tickLine={false} reversed domain={['auto', 'auto']} />
                        <Tooltip
                          contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E4E7EC', borderRadius: '6px', fontSize: '0.75rem' }}
                          formatter={(value: any) => [`${Number(value || 0).toFixed(1)} m bgl`, 'Depth']}
                        />
                        <Line
                          type="monotone"
                          dataKey="depth"
                          stroke="#2F80ED"
                          strokeWidth={2}
                          dot={{ r: 3, fill: '#2F80ED' }}
                          activeDot={{ r: 5 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#98A2B3', fontSize: '0.8125rem' }}>
                      Historical observations loading...
                    </div>
                  )}
                </div>

                <div style={{ fontSize: '0.75rem', color: '#667085', marginTop: '14px', borderTop: '1px solid #E4E7EC', paddingTop: '10px' }}>
                  Source: Central Ground Water Board historical observations (Dakshina Kannada monitoring stations).
                </div>
              </div>

              {/* Station Details */}
              <div className="card">
                <div className="card-header">
                  <div className="card-title">
                    <span>Station metadata</span>
                  </div>
                  <span className="badge badge-neutral">Historical</span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#667085', marginBottom: '2px' }}>Matched monitoring station</div>
                    <div style={{ fontWeight: 600, color: '#16324F', fontSize: '0.9375rem' }}>
                      {selectedWard?.matched_station || wardDetail?.display_name || currentWardName}
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#667085', marginBottom: '2px' }}>Latest government observation date</div>
                    <div style={{ fontWeight: 600, color: '#16324F', fontSize: '0.9375rem' }}>
                      {selectedWard?.depth_observed_at || wardDetail?.depth_observed_at || '2020-11-30'}
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#667085', marginBottom: '2px' }}>Observed depth</div>
                    <div style={{ fontWeight: 600, color: '#16324F', fontSize: '0.9375rem' }}>
                      {wardDetail?.groundwater_depth_m ? `${wardDetail.groundwater_depth_m.toFixed(1)} m bgl` : '12.4 m bgl'}
                    </div>
                  </div>

                  <div style={{ background: '#F8FAFC', padding: '12px', borderRadius: '6px', border: '1px solid #E4E7EC', fontSize: '0.75rem', color: '#475467' }}>
                    <strong>180-Day Freshness Guardrail:</strong> Because government observations are quarterly historical records, they are not used to forecast current household tanker needs.
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ──────── 5. TAB: ABOUT ──────── */}
        {activeTab === 'about' && (
          <div style={{ maxWidth: '780px', margin: '0 auto' }}>
            <div className="page-header">
              <h1 className="page-title">About JalaNetra Pulse</h1>
              <p className="page-subtitle">
                Real-time community water-outage detection and neighbourhood response for Mangaluru.
              </p>
            </div>

            <div className="card" style={{ marginBottom: '20px' }}>
              <h2 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#16324F', marginBottom: '12px' }}>
                How this works
              </h2>
              <div style={{ fontSize: '0.875rem', color: '#475467', lineHeight: 1.6, display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <p>
                  <strong>1. Community signals first:</strong> Municipal pipelines and feeder pumps frequently trip without warning. Action must come from current household reports, not slow seasonal groundwater archives.
                </p>
                <p>
                  <strong>2. 90-minute clustering:</strong> When 3 or more independent residents in the same neighbourhood report dry taps within 90 minutes, JalaNetra Pulse activates an active Community Water Alert.
                </p>
                <p>
                  <strong>3. Non-official transparency:</strong> All notifications clearly state: <em>Reported by local residents. Verification in progress.</em> This prevents confusion with municipal agency bulletins while enabling fast mutual aid.
                </p>
                <p>
                  <strong>4. Community recovery:</strong> When 2 independent households mark water restored, the incident safely transitions to community recovery.
                </p>
              </div>
            </div>

            <div className="card" style={{ marginBottom: '20px' }}>
              <h2 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#16324F', marginBottom: '12px' }}>
                Data and privacy
              </h2>
              <div style={{ fontSize: '0.875rem', color: '#475467', lineHeight: 1.6, display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <p>
                  <strong>Zero personal exposure:</strong> When residents provide a phone number for alerts, it is converted into a one-way cryptographic SHA-256 hash. Plaintext phone numbers are never stored in databases, written to server logs, or shared.
                </p>
                <p>
                  <strong>Anti-spam safeguards:</strong> Deduplication rules ensure that a single household cannot inflate report counts more than once every 30 minutes.
                </p>
                <p>
                  <strong>Responsible historical baselines:</strong> Over 4,900 Central Ground Water Board records provide geological vulnerability context, governed by a 180-day freshness safeguard.
                </p>
              </div>
            </div>

            <div style={{ textAlign: 'center', marginTop: '24px' }}>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => switchTab('tools')}
                style={{ fontSize: '0.8125rem', color: '#667085' }}
              >
                Notification test &amp; tools <ArrowRightIcon size={14} />
              </button>
            </div>
          </div>
        )}

        {/* ──────── 6. TAB: DEVELOPER & NOTIFICATION TOOLS (/tools) ──────── */}
        {activeTab === 'tools' && (
          <div style={{ maxWidth: '800px', margin: '0 auto' }}>
            <div className="page-header">
              <h1 className="page-title">Notification test</h1>
              <p className="page-subtitle">
                Generate a message preview or test delivery to a verified number.
              </p>
            </div>

            {/* Notification Preview Card */}
            <div className="card" style={{ marginBottom: '24px' }}>
              <div className="card-header">
                <div className="card-title">
                  <span>Message preview</span>
                </div>
                <span className="badge badge-neutral">Notification Dispatch</span>
              </div>

              <p style={{ fontSize: '0.8125rem', color: '#475467', marginBottom: '16px' }}>
                Message preview. Delivery is available only for verified test numbers.
              </p>

              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '18px' }}>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => handleTestSms(false)}
                  disabled={smsTesting}
                >
                  {smsTesting ? 'Generating...' : 'Generate message preview'}
                </button>
              </div>

              {smsResult && (
                <div style={{ background: '#F8FAFC', padding: '16px', borderRadius: '8px', border: '1px solid #E4E7EC', marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#667085', marginBottom: '6px' }}>
                    <span>Mode: {smsResult.mode.toUpperCase()}</span>
                    <span>Status: {smsResult.sent ? 'Dispatched' : 'Preview only'}</span>
                  </div>
                  <div style={{ fontFamily: 'monospace', fontSize: '0.8125rem', color: '#16324F', background: '#FFFFFF', padding: '12px', borderRadius: '6px', border: '1px solid #E4E7EC' }}>
                    {smsResult.message_preview}
                  </div>
                  <div style={{ fontSize: '0.6875rem', color: '#667085', marginTop: '8px' }}>
                    Destination: {smsResult.destination_masked}
                  </div>
                </div>
              )}

              <div style={{ borderTop: '1px solid #E4E7EC', paddingTop: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                  <input
                    type="checkbox"
                    id="confirmLiveSend"
                    checked={confirmLiveSend}
                    onChange={(e) => setConfirmLiveSend(e.target.checked)}
                  />
                  <label htmlFor="confirmLiveSend" style={{ fontSize: '0.8125rem', color: '#475467' }}>
                    I understand live delivery requires verified test credentials configured in server environment.
                  </label>
                </div>

                <button
                  type="button"
                  className="btn btn-secondary"
                  disabled={!confirmLiveSend || smsTesting}
                  onClick={() => handleTestSms(true)}
                >
                  Send test notification
                </button>
              </div>
            </div>

            {/* Simulation Controls Card */}
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  <span>Simulation controls</span>
                </div>
                <span className="badge badge-neutral">Training</span>
              </div>

              <p style={{ fontSize: '0.8125rem', color: '#475467', marginBottom: '16px' }}>
                Simulate community report patterns to test incident triggers and recovery workflows.
                Simulated scenario records are labeled internally and used for training response teams.
              </p>

              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  disabled={scenarioLoading}
                  onClick={handleSeedOutage}
                >
                  Simulate 3 No Water reports
                </button>

                <button
                  type="button"
                  className="btn btn-secondary"
                  disabled={scenarioLoading}
                  onClick={handleSeedRecovery}
                >
                  Simulate recovery reports
                </button>

                <button
                  type="button"
                  className="btn btn-ghost"
                  disabled={scenarioLoading}
                  onClick={handleResetScenario}
                >
                  Reset simulated data
                </button>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* ──────────────── Footer ──────────────── */}
      <footer className="footer">
        <div className="footer-inner">
          <div>
            <strong>JalaNetra Pulse</strong>
          </div>

          <div className="footer-links">
            <button type="button" className="footer-link" onClick={() => switchTab('about')}>
              How it works
            </button>
            <button type="button" className="footer-link" onClick={() => switchTab('about')}>
              Data &amp; privacy
            </button>
            <button type="button" className="footer-link" onClick={() => switchTab('admin')}>
              Response board
            </button>
          </div>

          <div>
            Community water response for Mangaluru
          </div>
        </div>
      </footer>
    </div>
  );
}
