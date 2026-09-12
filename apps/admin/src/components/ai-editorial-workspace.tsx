"use client";

import React, { useState } from "react";
import styles from "./ai-editorial-workspace.module.css";
import {
  AiEditorialApiClient,
  ExtractClaimsResponse,
  SuggestPerspectivesResponse,
  BiasCheckResponse,
  ComposeSummaryResponse,
} from "../lib/ai-editorial-api";

interface AiEditorialWorkspaceProps {
  apiClient?: AiEditorialApiClient;
}

export function AiEditorialWorkspace({ apiClient }: AiEditorialWorkspaceProps) {
  const [client] = useState(() => apiClient || new AiEditorialApiClient());
  const [activeTab, setActiveTab] = useState<
    "CLAIMS" | "PERSPECTIVES" | "BIAS" | "SUMMARY"
  >("CLAIMS");

  // Claims tab state
  const [sourceText, setSourceText] = useState(
    "Resmi verilere göre enerji maliyetleri bu yıl yüzde 25 arttı. Belediyeler toplu taşımayı sübvanse etmek zorundadır. Adaletli kaynak dağıtımı toplum için değerlidir."
  );
  const [claimsResult, setClaimsResult] =
    useState<ExtractClaimsResponse | null>(null);

  // Perspectives tab state
  const [dilemmaTitle, setDilemmaTitle] = useState(
    "Şehir Merkezinde Özel Araç Girişinin Sınırlandırılması"
  );
  const [contextSummary, setContextSummary] = useState(
    "Hava kalitesini artırmak ve trafik yoğunluğunu azaltmak amacıyla şehir merkezine ücretli giriş bölgesi getirilmesi önerilmektedir."
  );
  const [perspectivesResult, setPerspectivesResult] =
    useState<SuggestPerspectivesResponse | null>(null);

  // Bias tab state
  const [biasText, setBiasText] = useState(
    "Bu karar şüphesiz tam bir rezalet ve kabul edilemez bir dayatmadır."
  );
  const [biasResult, setBiasResult] = useState<BiasCheckResponse | null>(null);

  // Summary tab state
  const [summaryMaterial, setSummaryMaterial] = useState(
    "Karayolları Genel Müdürlüğü tarafından yürütülen çalışmalar sonucunda, kış aylarında meydana gelen buzlanma riskine karşı yeni sensör ağlarının otoyollara yerleştirilmesi kararlaştırıldı."
  );
  const [summaryResult, setSummaryResult] =
    useState<ComposeSummaryResponse | null>(null);

  const handleExtractClaims = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await client.extractClaims(sourceText);
      setClaimsResult(res);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Extraction failed");
    }
  };

  const handleSuggestPerspectives = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await client.suggestPerspectives(dilemmaTitle, contextSummary);
      setPerspectivesResult(res);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Perspective suggestion failed");
    }
  };

  const handleCheckBias = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await client.checkBias(biasText);
      setBiasResult(res);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Bias check failed");
    }
  };

  const handleComposeSummary = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await client.composeSummary(summaryMaterial, 250);
      setSummaryResult(res);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Summary composition failed");
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>AI-Assisted Editorial Studio (CAP-060)</h1>
        <p className={styles.subtitle}>
          Provider-neutral AI assistance: claim extraction, balanced perspective generation, bias auditing and summary drafting.
        </p>
      </div>

      <div className={styles.disclaimerBanner}>
        ⚠️ <strong>Editorial Invariant:</strong> AI output is strictly advisory. AI cannot autonomously publish or validate cases without explicit human editor review.
      </div>

      <div className={styles.tabs}>
        <button
          className={`${styles.tabBtn} ${
            activeTab === "CLAIMS" ? styles.activeTab : ""
          }`}
          onClick={() => setActiveTab("CLAIMS")}
        >
          Claim Extraction
        </button>
        <button
          className={`${styles.tabBtn} ${
            activeTab === "PERSPECTIVES" ? styles.activeTab : ""
          }`}
          onClick={() => setActiveTab("PERSPECTIVES")}
        >
          Perspective Suggestion
        </button>
        <button
          className={`${styles.tabBtn} ${
            activeTab === "BIAS" ? styles.activeTab : ""
          }`}
          onClick={() => setActiveTab("BIAS")}
        >
          Neutrality & Bias Audit
        </button>
        <button
          className={`${styles.tabBtn} ${
            activeTab === "SUMMARY" ? styles.activeTab : ""
          }`}
          onClick={() => setActiveTab("SUMMARY")}
        >
          Summary Composer
        </button>
      </div>

      {activeTab === "CLAIMS" && (
        <div className={styles.grid}>
          <div className={styles.card}>
            <h2 className={styles.cardTitle}>Extract Claims from Raw Source</h2>
            <form onSubmit={handleExtractClaims}>
              <div className={styles.formGroup}>
                <label className={styles.label}>Source / Article Text</label>
                <textarea
                  className={styles.textarea}
                  value={sourceText}
                  onChange={(e) => setSourceText(e.target.value)}
                  rows={5}
                  required
                />
              </div>
              <button type="submit" className={styles.submitBtn}>
                Run AI Claim Extraction
              </button>
            </form>

            {claimsResult && (
              <div className={styles.resultBox}>
                <h3>Extracted Claims ({claimsResult.extracted_claims.length})</h3>
                {claimsResult.extracted_claims.map((c, i) => (
                  <div key={i} className={styles.claimCard}>
                    <div>
                      <span
                        className={`${styles.badge} ${
                          c.claim_type === "FACTUAL"
                            ? styles.badgeFactual
                            : styles.badgeNormative
                        }`}
                      >
                        {c.claim_type}
                      </span>
                      <small style={{ color: "#94a3b8" }}>
                        Confidence: {(c.confidence_score * 100).toFixed(0)}%
                      </small>
                    </div>
                    <p style={{ marginTop: "0.5rem", marginBottom: "0.25rem" }}>
                      {c.claim_text}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === "PERSPECTIVES" && (
        <div className={styles.grid}>
          <div className={styles.card}>
            <h2 className={styles.cardTitle}>Generate Balanced Perspectives</h2>
            <form onSubmit={handleSuggestPerspectives}>
              <div className={styles.formGroup}>
                <label className={styles.label}>Dilemma Title</label>
                <input
                  className={styles.input}
                  value={dilemmaTitle}
                  onChange={(e) => setDilemmaTitle(e.target.value)}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>Context Summary</label>
                <textarea
                  className={styles.textarea}
                  value={contextSummary}
                  onChange={(e) => setContextSummary(e.target.value)}
                  rows={3}
                  required
                />
              </div>
              <button type="submit" className={styles.submitBtn}>
                Suggest Thesis, Antithesis & Bridge
              </button>
            </form>

            {perspectivesResult && (
              <div className={styles.resultBox}>
                <h3>Suggested Perspectives (Entropy: {perspectivesResult.balance_entropy})</h3>
                {perspectivesResult.perspectives.map((p, i) => (
                  <div key={i} className={styles.claimCard}>
                    <strong>
                      {p.orientation}: {p.perspective_label}
                    </strong>
                    <p style={{ margin: "0.25rem 0", color: "#cbd5e1" }}>
                      {p.core_argument}
                    </p>
                    <small style={{ color: "#38bdf8" }}>
                      Value: {p.underlying_value}
                    </small>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === "BIAS" && (
        <div className={styles.grid}>
          <div className={styles.card}>
            <h2 className={styles.cardTitle}>Check Language Neutrality & Bias</h2>
            <form onSubmit={handleCheckBias}>
              <div className={styles.formGroup}>
                <label className={styles.label}>Draft Text to Inspect</label>
                <textarea
                  className={styles.textarea}
                  value={biasText}
                  onChange={(e) => setBiasText(e.target.value)}
                  rows={4}
                  required
                />
              </div>
              <button type="submit" className={styles.submitBtn}>
                Run Neutrality Audit
              </button>
            </form>

            {biasResult && (
              <div className={styles.resultBox}>
                <h3>Audit Result: {biasResult.is_neutral ? "NEUTRAL" : "LOADED TERMS DETECTED"}</h3>
                <p>
                  <strong>Neutrality Score:</strong>{" "}
                  {(biasResult.neutrality_score * 100).toFixed(0)}%
                </p>
                {biasResult.flagged_terms.length > 0 && (
                  <div>
                    <strong>Flagged Terms & Neutral Suggestions:</strong>
                    <ul>
                      {biasResult.flagged_terms.map((t) => (
                        <li key={t}>
                          <span style={{ color: "#ef4444" }}>&quot;{t}&quot;</span> &rarr;{" "}
                          <span style={{ color: "#10b981" }}>
                            &quot;{biasResult.suggested_neutral_rephrasings[t] || "daha nötr bir ifade"}&quot;
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === "SUMMARY" && (
        <div className={styles.grid}>
          <div className={styles.card}>
            <h2 className={styles.cardTitle}>Compose Non-Normative Summary</h2>
            <form onSubmit={handleComposeSummary}>
              <div className={styles.formGroup}>
                <label className={styles.label}>Long Raw Material</label>
                <textarea
                  className={styles.textarea}
                  value={summaryMaterial}
                  onChange={(e) => setSummaryMaterial(e.target.value)}
                  rows={5}
                  required
                />
              </div>
              <button type="submit" className={styles.submitBtn}>
                Compose Summary
              </button>
            </form>

            {summaryResult && (
              <div className={styles.resultBox}>
                <h3>Draft Summary ({summaryResult.character_count} chars)</h3>
                <p style={{ background: "#0f172a", padding: "1rem", borderRadius: "0.25rem" }}>
                  {summaryResult.composed_summary}
                </p>
                <small style={{ color: "#94a3b8" }}>
                  Readability Index: {summaryResult.readability_index}
                </small>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
