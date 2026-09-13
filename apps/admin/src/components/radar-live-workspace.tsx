"use client";

import React, { useEffect, useState } from "react";
import styles from "./radar-live-workspace.module.css";
import {
  RadarLiveApiClient,
  LiveRadarResponse,
  ContextDriftNoticeResponse,
  ContextDriftType,
  DriftRecommendedAction,
} from "../lib/radar-live-api";

interface RadarLiveWorkspaceProps {
  apiClient?: RadarLiveApiClient;
}

export function RadarLiveWorkspace({ apiClient }: RadarLiveWorkspaceProps) {
  const [client] = useState(() => apiClient || new RadarLiveApiClient());
  const [caseId, setCaseId] = useState("00000000-0000-0000-0000-000000000001");
  const [radar, setRadar] = useState<LiveRadarResponse | null>(null);
  const [notices, setNotices] = useState<ContextDriftNoticeResponse[]>([]);

  // Publish notice form state
  const [driftType, setDriftType] = useState<ContextDriftType>("LEGAL_REFORM");
  const [summary, setSummary] = useState(
    "İlgili yönetmelik maddesi Resmi Gazetede yayımlanan kararla güncellenmiştir."
  );
  const [action, setAction] =
    useState<DriftRecommendedAction>("CONTINUE_WITH_AWARENESS");
  const [sourceUrl, setSourceUrl] = useState("https://resmigazete.gov.tr/2026/09/10");

  useEffect(() => {
    client.getLiveRadar(caseId).then(setRadar);
    client.getDriftNotices(caseId).then(setNotices);
  }, [client, caseId]);

  const handlePublishNotice = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await client.publishDriftNotice(caseId, {
        drift_type: driftType,
        summary,
        recommended_action: action,
        source_reference_url: sourceUrl,
      });
      const updated = await client.getDriftNotices(caseId);
      setNotices(updated);
      alert("Context Drift Notice published successfully!");
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Publishing failed");
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>Live Radar & Context Drift Intelligence (CAP-076)</h1>
        <p className={styles.subtitle}>
          Real-time deliberation momentum, demographic shift vectors and legal/factual drift notice publishing.
        </p>
      </div>

      {/* Top Stat Cards */}
      <div className={styles.gridStats}>
        <div className={styles.statCard}>
          <h3 className={styles.statTitle}>Deliberation Velocity</h3>
          <p className={styles.statValue}>
            {radar ? (radar.deliberation_velocity_index * 100).toFixed(0) : "..."}%
          </p>
          <p className={styles.statCaption}>Current discussion resonance speed</p>
        </div>
        <div className={styles.statCard}>
          <h3 className={styles.statTitle}>Live Participants</h3>
          <p className={styles.statValue}>
            {radar ? radar.live_participant_count.toLocaleString() : "..."}
          </p>
          <p className={styles.statCaption}>Active concurrent weighers</p>
        </div>
        <div className={styles.statCard}>
          <h3 className={styles.statTitle}>Consensus Momentum</h3>
          <p className={styles.statValue} style={{ fontSize: "1.25rem", color: "#10b981" }}>
            {radar ? radar.primary_consensus_momentum : "..."}
          </p>
          <p className={styles.statCaption}>Primary community vector</p>
        </div>
        <div className={styles.statCard}>
          <h3 className={styles.statTitle}>Active Context Drift</h3>
          <p
            className={styles.statValue}
            style={{
              fontSize: "1.25rem",
              color: notices.length > 0 ? "#f59e0b" : "#38bdf8",
            }}
          >
            {notices.length > 0 ? `${notices.length} DRIFT ALERTS` : "NOMINAL"}
          </p>
          <p className={styles.statCaption}>Governed legislative/factual shifts</p>
        </div>
      </div>

      <div className={styles.gridSections}>
        {/* Demographic Shift Vectors */}
        <div className={styles.card}>
          <h2 className={styles.cardTitle}>Demographic Shift Vectors</h2>
          {radar ? (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th className={styles.th}>Demographic Segment</th>
                  <th className={styles.th}>Support Delta</th>
                  <th className={styles.th}>Confidence Interval</th>
                </tr>
              </thead>
              <tbody>
                {radar.shift_vectors.map((vec) => (
                  <tr key={vec.demographic_segment}>
                    <td className={styles.td}>
                      <strong>{vec.demographic_segment}</strong>
                    </td>
                    <td
                      className={styles.td}
                      style={{
                        color: vec.support_delta_percentage >= 0 ? "#10b981" : "#ef4444",
                      }}
                    >
                      {vec.support_delta_percentage >= 0 ? "+" : ""}
                      {vec.support_delta_percentage.toFixed(1)}%
                    </td>
                    <td className={styles.td}>
                      {(vec.confidence_interval * 100).toFixed(0)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>Loading shift vectors...</p>
          )}

          <div style={{ marginTop: "1.5rem" }}>
            <h3 style={{ fontSize: "1rem", marginBottom: "0.75rem" }}>
              Active Context Drift Notices ({notices.length})
            </h3>
            {notices.map((n) => (
              <div key={n.notice_id} className={styles.noticeItem}>
                <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.25rem" }}>
                  <span className={`${styles.badge} ${styles.badgeReform}`}>
                    {n.drift_type}
                  </span>
                  <span className={`${styles.badge} ${styles.badgeAction}`}>
                    {n.recommended_action}
                  </span>
                </div>
                <p style={{ margin: "0.25rem 0", color: "#f8fafc" }}>{n.summary}</p>
                {n.source_reference_url && (
                  <small style={{ color: "#38bdf8" }}>
                    Source: {n.source_reference_url}
                  </small>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Publish Drift Notice Form */}
        <div className={styles.card}>
          <h2 className={styles.cardTitle}>Publish Context Drift Notice</h2>
          <form onSubmit={handlePublishNotice}>
            <div className={styles.formGroup}>
              <label className={styles.label}>Case Version ID</label>
              <input
                className={styles.input}
                value={caseId}
                onChange={(e) => setCaseId(e.target.value)}
                required
              />
            </div>
            <div className={styles.formGroup}>
              <label className={styles.label}>Drift Type</label>
              <select
                className={styles.select}
                value={driftType}
                onChange={(e) => setDriftType(e.target.value as ContextDriftType)}
              >
                <option value="LEGAL_REFORM">LEGAL_REFORM (Yasal Değişiklik)</option>
                <option value="FACTUAL_UPDATE">FACTUAL_UPDATE (Olgusal Güncelleme)</option>
                <option value="ASSUMPTION_CHANGED">ASSUMPTION_CHANGED (Varsayım Değişimi)</option>
                <option value="SUPERSEDED_BASELINE">SUPERSEDED_BASELINE (Eski Taban)</option>
              </select>
            </div>
            <div className={styles.formGroup}>
              <label className={styles.label}>Recommended Action for Participants</label>
              <select
                className={styles.select}
                value={action}
                onChange={(e) => setAction(e.target.value as DriftRecommendedAction)}
              >
                <option value="CONTINUE_WITH_AWARENESS">CONTINUE_WITH_AWARENESS</option>
                <option value="REVIEW_AMENDMENT">REVIEW_AMENDMENT</option>
                <option value="CASE_SUPERSEDED">CASE_SUPERSEDED</option>
              </select>
            </div>
            <div className={styles.formGroup}>
              <label className={styles.label}>Notice Summary</label>
              <textarea
                className={styles.textarea}
                value={summary}
                onChange={(e) => setSummary(e.target.value)}
                rows={3}
                required
              />
            </div>
            <div className={styles.formGroup}>
              <label className={styles.label}>Source Reference URL</label>
              <input
                className={styles.input}
                value={sourceUrl}
                onChange={(e) => setSourceUrl(e.target.value)}
              />
            </div>
            <button type="submit" className={styles.submitBtn}>
              Publish Drift Notice (KEFE-CONTEXT-DRIFT-001)
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
