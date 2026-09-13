"use client";

import React, { useEffect, useState } from "react";
import styles from "./trust-integrity-workspace.module.css";
import {
  TrustIntegrityApiClient,
  QuarantineClusterRecord,
  ClusterInspectionResponse,
  AgendaThresholdEvaluationResponse,
} from "../lib/trust-integrity-api";

interface TrustIntegrityWorkspaceProps {
  apiClient?: TrustIntegrityApiClient;
}

export function TrustIntegrityWorkspace({
  apiClient,
}: TrustIntegrityWorkspaceProps) {
  const [client] = useState(
    () => apiClient || new TrustIntegrityApiClient()
  );
  const [activeTab, setActiveTab] = useState<
    "SHIELD" | "AGENDA" | "REGISTRY"
  >("SHIELD");

  // Shield state
  const [clusterId, setClusterId] = useState("cluster_sweep_01");
  const [targetCaseId, setTargetCaseId] = useState("case_ai_001");
  const [syntheticScore, setSyntheticScore] = useState(0.85);
  const [quarantinedCount, setQuarantinedCount] = useState(450);
  const [semanticEntropy, setSemanticEntropy] = useState(0.18);
  const [inspectionResult, setInspectionResult] =
    useState<ClusterInspectionResponse | null>(null);

  // Agenda state
  const [topicId, setTopicId] = useState("topic_water_crisis");
  const [topicTitle, setTopicTitle] = useState("Water Infrastructure & Safety");
  const [velocityIndex, setVelocityIndex] = useState(0.82);
  const [diversityEntropy, setDiversityEntropy] = useState(0.74);
  const [agendaResult, setAgendaResult] =
    useState<AgendaThresholdEvaluationResponse | null>(null);

  // Registry state
  const [clusters, setClusters] = useState<QuarantineClusterRecord[]>([]);

  useEffect(() => {
    client.listClusters().then(setClusters);
  }, [client]);

  const handleInspect = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await client.inspectCluster({
        cluster_id: clusterId,
        target_case_id: targetCaseId,
        synthetic_probability_score: Number(syntheticScore),
        quarantined_bot_payloads_count: Number(quarantinedCount),
        semantic_entropy_index: Number(semanticEntropy),
      });
      setInspectionResult(res);
      const updated = await client.listClusters();
      setClusters(updated);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Inspection failed");
    }
  };

  const handleEvaluateAgenda = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await client.evaluateAgenda({
        topic_id: topicId,
        topic_title: topicTitle,
        resonance_velocity_index: Number(velocityIndex),
        viewpoint_diversity_entropy: Number(diversityEntropy),
      });
      setAgendaResult(res);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Agenda evaluation failed");
    }
  };

  const handleStatusChange = async (
    id: string,
    status: "ACTIVE" | "RESOLVED" | "WHITELISTED"
  ) => {
    try {
      await client.updateClusterStatus(id, status);
      const updated = await client.listClusters();
      setClusters(updated);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Status update failed");
    }
  };

  const getBadgeClass = (state: string) => {
    if (state === "ISOLATED_QUARANTINE_SWARM") return styles.badgeQuarantine;
    if (state === "SUSPECTED_BOT_COORDINATION") return styles.badgeSuspected;
    return styles.badgeOrganic;
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>Trust, Bot & Anomaly Integrity Shield</h1>
        <p className={styles.subtitle}>
          Synthetic astroturfing defense, sybil immunity and dynamic agenda priority surfacing (CAP-073).
        </p>
      </div>

      <div className={styles.tabs}>
        <button
          className={`${styles.tabBtn} ${
            activeTab === "SHIELD" ? styles.activeTab : ""
          }`}
          onClick={() => setActiveTab("SHIELD")}
        >
          Bot Defense Inspection
        </button>
        <button
          className={`${styles.tabBtn} ${
            activeTab === "AGENDA" ? styles.activeTab : ""
          }`}
          onClick={() => setActiveTab("AGENDA")}
        >
          Agenda Thresholding
        </button>
        <button
          className={`${styles.tabBtn} ${
            activeTab === "REGISTRY" ? styles.activeTab : ""
          }`}
          onClick={() => setActiveTab("REGISTRY")}
        >
          Quarantine Registry ({clusters.length})
        </button>
      </div>

      {activeTab === "SHIELD" && (
        <div className={styles.grid}>
          <div className={styles.card}>
            <h2 className={styles.cardTitle}>Inspect Suspected Cluster</h2>
            <form onSubmit={handleInspect}>
              <div className={styles.formGroup}>
                <label className={styles.label}>Cluster Identifier</label>
                <input
                  className={styles.input}
                  value={clusterId}
                  onChange={(e) => setClusterId(e.target.value)}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>Target Case ID</label>
                <input
                  className={styles.input}
                  value={targetCaseId}
                  onChange={(e) => setTargetCaseId(e.target.value)}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>
                  Synthetic Probability Score: {syntheticScore}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={syntheticScore}
                  onChange={(e) => setSyntheticScore(parseFloat(e.target.value))}
                />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>
                  Quarantined Bot Payloads Count
                </label>
                <input
                  type="number"
                  className={styles.input}
                  value={quarantinedCount}
                  onChange={(e) => setQuarantinedCount(parseInt(e.target.value, 10))}
                  min="0"
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>
                  Semantic Entropy Index: {semanticEntropy}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={semanticEntropy}
                  onChange={(e) => setSemanticEntropy(parseFloat(e.target.value))}
                />
              </div>
              <button type="submit" className={styles.submitBtn}>
                Run Shield Inspection
              </button>
            </form>

            {inspectionResult && (
              <div className={styles.resultBox}>
                <h3>Inspection Result</h3>
                <p>
                  <strong>Defense State:</strong>{" "}
                  <span
                    className={`${styles.badge} ${getBadgeClass(
                      inspectionResult.defense_state
                    )}`}
                  >
                    {inspectionResult.defense_state}
                  </span>
                </p>
                <p>
                  <strong>Quarantine Action:</strong>{" "}
                  {inspectionResult.is_quarantined
                    ? "AUTOMATICALLY ISOLATED"
                    : "PASSIVE MONITORING"}
                </p>
                <p>
                  <strong>Payloads Isolated:</strong>{" "}
                  {inspectionResult.quarantined_bot_payloads_count}
                </p>
              </div>
            )}
          </div>

          <div className={styles.card}>
            <h2 className={styles.cardTitle}>Shield Invariants & Gates</h2>
            <ul style={{ paddingLeft: "1.25rem", lineHeight: "1.75" }}>
              <li>
                <strong>Thresholds:</strong> Synthetic score &ge; 0.80 and Semantic Entropy &lt; 0.25 triggers automatic quarantine.
              </li>
              <li>
                <strong>Suspected Coordination:</strong> Synthetic score &ge; 0.40 triggers targeted rate throttling.
              </li>
              <li>
                <strong>Organic Authentic:</strong> Passed without restriction.
              </li>
              <li>
                <strong>Zero Algorithmic Rage:</strong> Outburst velocity alone cannot push unverified issues to national ballot without entropy check.
              </li>
            </ul>
          </div>
        </div>
      )}

      {activeTab === "AGENDA" && (
        <div className={styles.grid}>
          <div className={styles.card}>
            <h2 className={styles.cardTitle}>Evaluate Agenda Thresholding</h2>
            <form onSubmit={handleEvaluateAgenda}>
              <div className={styles.formGroup}>
                <label className={styles.label}>Topic ID</label>
                <input
                  className={styles.input}
                  value={topicId}
                  onChange={(e) => setTopicId(e.target.value)}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>Topic Title</label>
                <input
                  className={styles.input}
                  value={topicTitle}
                  onChange={(e) => setTopicTitle(e.target.value)}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>
                  Resonance Velocity Index: {velocityIndex}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={velocityIndex}
                  onChange={(e) => setVelocityIndex(parseFloat(e.target.value))}
                />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>
                  Viewpoint Diversity Entropy: {diversityEntropy}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={diversityEntropy}
                  onChange={(e) => setDiversityEntropy(parseFloat(e.target.value))}
                />
              </div>
              <button type="submit" className={styles.submitBtn}>
                Evaluate Priority Tier
              </button>
            </form>

            {agendaResult && (
              <div className={styles.resultBox}>
                <h3>Evaluation Result</h3>
                <p>
                  <strong>Priority Tier:</strong>{" "}
                  <span className={styles.badge}>
                    {agendaResult.priority_tier}
                  </span>
                </p>
                <p>
                  <strong>Featured on National Ballot:</strong>{" "}
                  {agendaResult.is_featured_on_national_ballot ? "YES" : "NO"}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === "REGISTRY" && (
        <div className={styles.card}>
          <h2 className={styles.cardTitle}>Quarantined & Monitored Clusters</h2>
          <table className={styles.table}>
            <thead>
              <tr>
                <th className={styles.th}>Cluster ID</th>
                <th className={styles.th}>Case ID</th>
                <th className={styles.th}>Defense State</th>
                <th className={styles.th}>Synthetic Prob</th>
                <th className={styles.th}>Quarantined Payloads</th>
                <th className={styles.th}>Status</th>
                <th className={styles.th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {clusters.map((c) => (
                <tr key={c.cluster_id}>
                  <td className={styles.td}>{c.cluster_id}</td>
                  <td className={styles.td}>{c.target_case_id}</td>
                  <td className={styles.td}>
                    <span
                      className={`${styles.badge} ${getBadgeClass(
                        c.defense_state
                      )}`}
                    >
                      {c.defense_state}
                    </span>
                  </td>
                  <td className={styles.td}>{c.synthetic_probability_score}</td>
                  <td className={styles.td}>{c.quarantined_bot_payloads_count}</td>
                  <td className={styles.td}>{c.quarantine_status}</td>
                  <td className={styles.td}>
                    {c.quarantine_status === "ACTIVE" ? (
                      <button
                        className={styles.actionBtn}
                        onClick={() =>
                          handleStatusChange(c.cluster_id, "RESOLVED")
                        }
                      >
                        Resolve
                      </button>
                    ) : (
                      <button
                        className={styles.actionBtn}
                        onClick={() =>
                          handleStatusChange(c.cluster_id, "ACTIVE")
                        }
                      >
                        Quarantine
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
