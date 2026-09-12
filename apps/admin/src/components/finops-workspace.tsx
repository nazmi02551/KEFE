"use client";

import React, { useEffect, useState } from "react";
import styles from "./finops-workspace.module.css";
import {
  FinOpsApiClient,
  FinOpsSummaryResponse,
  FinOpsBreakdownResponse,
  FinOpsSimulateResponse,
} from "../lib/finops-api";

interface FinOpsWorkspaceProps {
  apiClient?: FinOpsApiClient;
}

export function FinOpsWorkspace({ apiClient }: FinOpsWorkspaceProps) {
  const [client] = useState(() => apiClient || new FinOpsApiClient());
  const [summary, setSummary] = useState<FinOpsSummaryResponse | null>(null);
  const [breakdown, setBreakdown] = useState<FinOpsBreakdownResponse | null>(null);

  // Simulation state
  const [simWau, setSimWau] = useState(50000);
  const [simWeighsPerUser, setSimWeighsPerUser] = useState(4);
  const [simResult, setSimResult] = useState<FinOpsSimulateResponse | null>(null);

  useEffect(() => {
    client.getSummary().then(setSummary);
    client.getBreakdown().then(setBreakdown);
  }, [client]);

  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await client.simulateScale(
        Number(simWau),
        Number(simWeighsPerUser)
      );
      setSimResult(res);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Simulation failed");
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>FinOps & Provider Cost Intelligence (CAP-124)</h1>
        <p className={styles.subtitle}>
          Unit economics, Cost per Weigh (CPW), token utilization, SMS OTP spend and scale projections.
        </p>
      </div>

      {/* Top Stat Cards */}
      <div className={styles.gridStats}>
        <div className={styles.statCard}>
          <h3 className={styles.statTitle}>Cost Per Weigh (CPW)</h3>
          <p className={styles.statValue}>
            {summary ? `$${summary.cost_per_weigh_usd.toFixed(3)}` : "..."}
          </p>
          <p className={styles.statCaption}>Weighted average unit cost per decision</p>
        </div>
        <div className={styles.statCard}>
          <h3 className={styles.statTitle}>Total Monthly Spend</h3>
          <p className={styles.statValue}>
            {summary ? `$${summary.total_monthly_spend_usd.toFixed(2)}` : "..."}
          </p>
          <p className={styles.statCaption}>All cloud, model & telephony providers</p>
        </div>
        <div className={styles.statCard}>
          <h3 className={styles.statTitle}>Tokens Consumed</h3>
          <p className={styles.statValue}>
            {summary ? summary.total_tokens_consumed.toLocaleString() : "..."}
          </p>
          <p className={styles.statCaption}>Inference & embedding token volume</p>
        </div>
        <div className={styles.statCard}>
          <h3 className={styles.statTitle}>Latency (p95)</h3>
          <p className={styles.statValue}>
            {summary ? `${summary.p95_latency_ms} ms` : "..."}
          </p>
          <p className={styles.statCaption}>Provider response time at 95th percentile</p>
        </div>
      </div>

      <div className={styles.gridSections}>
        {/* Provider Breakdown Table */}
        <div className={styles.card}>
          <h2 className={styles.cardTitle}>Provider Spend Breakdown</h2>
          {breakdown ? (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th className={styles.th}>Provider Service</th>
                  <th className={styles.th}>Category</th>
                  <th className={styles.th}>Monthly Spend</th>
                  <th className={styles.th}>Share</th>
                  <th className={styles.th}>Rate Metric</th>
                </tr>
              </thead>
              <tbody>
                {breakdown.items.map((item) => (
                  <tr key={item.provider_name}>
                    <td className={styles.td}>
                      <strong>{item.provider_name}</strong>
                    </td>
                    <td className={styles.td}>{item.category}</td>
                    <td className={styles.td}>${item.monthly_cost_usd.toFixed(2)}</td>
                    <td className={styles.td}>{item.percentage_of_total.toFixed(1)}%</td>
                    <td className={styles.td}>{item.unit_metric}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>Loading breakdown data...</p>
          )}
        </div>

        {/* Scale Simulator */}
        <div className={styles.card}>
          <h2 className={styles.cardTitle}>Unit Economics Scale Simulator</h2>
          <form onSubmit={handleSimulate}>
            <div className={styles.formGroup}>
              <label className={styles.label}>Projected Monthly WAU</label>
              <input
                type="number"
                className={styles.input}
                value={simWau}
                onChange={(e) => setSimWau(parseInt(e.target.value, 10))}
                min="100"
                max="10000000"
                required
              />
            </div>
            <div className={styles.formGroup}>
              <label className={styles.label}>Avg Weighs per User / Month</label>
              <input
                type="number"
                className={styles.input}
                value={simWeighsPerUser}
                onChange={(e) => setSimWeighsPerUser(parseInt(e.target.value, 10))}
                min="1"
                max="50"
                required
              />
            </div>
            <button type="submit" className={styles.submitBtn}>
              Calculate Unit Economics
            </button>
          </form>

          {simResult && (
            <div className={styles.resultBox}>
              <h3>Projection at {simResult.projected_monthly_wau.toLocaleString()} WAU</h3>
              <p>
                <strong>Total Projected Weighs:</strong>{" "}
                {simResult.total_projected_weighs.toLocaleString()}
              </p>
              <p>
                <strong>Projected Monthly Cost:</strong> $
                {simResult.projected_monthly_cost_usd.toLocaleString()}
              </p>
              <p>
                <strong>Projected CPW:</strong> $
                {simResult.projected_cost_per_weigh_usd.toFixed(4)} / weigh
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
