"use client";

import React, { useEffect, useState } from "react";
import styles from "./analytics-metrics-workspace.module.css";
import {
  AnalyticsMetricsApiClient,
  NorthStarResponse,
  ActivationFunnelResponse,
  QualityResilienceResponse,
  DepolarizationEvaluationResponse,
} from "../lib/analytics-metrics-api";

interface AnalyticsMetricsWorkspaceProps {
  apiClient?: AnalyticsMetricsApiClient;
}

export function AnalyticsMetricsWorkspace({
  apiClient,
}: AnalyticsMetricsWorkspaceProps) {
  const [client] = useState(
    () => apiClient || new AnalyticsMetricsApiClient()
  );

  const [windowDays, setWindowDays] = useState(7);
  const [northStar, setNorthStar] = useState<NorthStarResponse | null>(null);
  const [funnel, setFunnel] = useState<ActivationFunnelResponse | null>(null);
  const [quality, setQuality] = useState<QualityResilienceResponse | null>(null);

  // Depolarization tester state
  const [caseId, setCaseId] = useState("00000000-0000-0000-0000-000000000001");
  const [preDistance, setPreDistance] = useState(0.85);
  const [postDistance, setPostDistance] = useState(0.35);
  const [depolResult, setDepolResult] =
    useState<DepolarizationEvaluationResponse | null>(null);

  useEffect(() => {
    client.getNorthStar(windowDays).then(setNorthStar);
    client.getActivationFunnel(windowDays).then(setFunnel);
    client.getQualityMetrics(windowDays).then(setQuality);
  }, [client, windowDays]);

  const handleEvaluateDepol = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await client.evaluateDepolarization({
        case_version_id: caseId,
        pre_deliberation_distance: Number(preDistance),
        post_deliberation_distance: Number(postDistance),
      });
      setDepolResult(res);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Depolarization evaluation failed");
    }
  };

  const getBadgeClass = (state: string) => {
    if (state === "HIGH_DEPOLARIZATION") return styles.badgeHigh;
    if (state === "MODERATE_BRIDGE_RESONANCE") return styles.badgeModerate;
    return styles.badgePersistent;
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h1 className={styles.title}>Analytics & Depolarization Metrics</h1>
            <p className={styles.subtitle}>
              North Star WAU, Activation Funnel, Quality Resilience and Bridge Efficacy (CAP-114..117).
            </p>
          </div>
          <div className={styles.controls}>
            <label className={styles.label}>Observation Window:</label>
            <select
              className={styles.select}
              value={windowDays}
              onChange={(e) => setWindowDays(parseInt(e.target.value, 10))}
            >
              <option value="7">Last 7 Days</option>
              <option value="14">Last 14 Days</option>
              <option value="30">Last 30 Days</option>
            </select>
          </div>
        </div>
      </div>

      {/* North Star Stats Grid */}
      <div className={styles.gridStats}>
        <div className={styles.statCard}>
          <h3 className={styles.statTitle}>Meaningful Weighs (MW)</h3>
          <p className={styles.statValue}>
            {northStar ? northStar.meaningful_weigh_count.toLocaleString() : "..."}
          </p>
          <p className={styles.statCaption}>Committed weighs within window (CAP-114)</p>
        </div>
        <div className={styles.statCard}>
          <h3 className={styles.statTitle}>Weekly Active Weighers (WAU)</h3>
          <p className={styles.statValue}>
            {northStar ? northStar.weekly_active_weighers.toLocaleString() : "..."}
          </p>
          <p className={styles.statCaption}>Distinct deliberating actors (CAP-114)</p>
        </div>
        <div className={styles.statCard}>
          <h3 className={styles.statTitle}>Cases Weighed</h3>
          <p className={styles.statValue}>
            {northStar ? northStar.distinct_cases_weighed : "..."}
          </p>
          <p className={styles.statCaption}>Unique active case versions</p>
        </div>
        <div className={styles.statCard}>
          <h3 className={styles.statTitle}>Resilience Index</h3>
          <p className={styles.statValue}>
            {quality ? `${(quality.resilience_index * 100).toFixed(1)}%` : "..."}
          </p>
          <p className={styles.statCaption}>
            Decisions held post-perspective (CAP-116)
          </p>
        </div>
      </div>

      <div className={styles.gridSections}>
        {/* Activation Funnel */}
        <div className={styles.card}>
          <h2 className={styles.cardTitle}>Activation Funnel (CAP-115)</h2>
          {funnel ? (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th className={styles.th}>Stage</th>
                  <th className={styles.th}>Sessions</th>
                  <th className={styles.th}>Conversion Rate</th>
                  <th className={styles.th}>Drop-off</th>
                </tr>
              </thead>
              <tbody>
                {funnel.stages.map((stage) => (
                  <tr key={stage.stage_name}>
                    <td className={styles.td}>
                      <strong>{stage.stage_name}</strong>
                    </td>
                    <td className={styles.td}>{stage.stage_count.toLocaleString()}</td>
                    <td className={styles.td}>
                      {(stage.conversion_from_start_rate * 100).toFixed(1)}%
                    </td>
                    <td className={styles.td}>
                      {(stage.drop_off_from_previous_rate * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>Loading funnel data...</p>
          )}
        </div>

        {/* Depolarization Calculator */}
        <div className={styles.card}>
          <h2 className={styles.cardTitle}>Depolarization Index Evaluator (CAP-117)</h2>
          <form onSubmit={handleEvaluateDepol}>
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
              <label className={styles.label}>
                Pre-Deliberation Distance: {preDistance}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={preDistance}
                onChange={(e) => setPreDistance(parseFloat(e.target.value))}
              />
            </div>
            <div className={styles.formGroup}>
              <label className={styles.label}>
                Post-Deliberation Distance: {postDistance}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={postDistance}
                onChange={(e) => setPostDistance(parseFloat(e.target.value))}
              />
            </div>
            <button type="submit" className={styles.submitBtn}>
              Calculate Bridge Efficacy
            </button>
          </form>

          {depolResult && (
            <div className={styles.resultBox}>
              <h3>Evaluation Result</h3>
              <p>
                <strong>Depolarization Score:</strong>{" "}
                {(depolResult.depolarization_score * 100).toFixed(1)}%
              </p>
              <p>
                <strong>Bridge Efficacy State:</strong>{" "}
                <span
                  className={`${styles.badge} ${getBadgeClass(
                    depolResult.bridge_efficacy_state
                  )}`}
                >
                  {depolResult.bridge_efficacy_state}
                </span>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
