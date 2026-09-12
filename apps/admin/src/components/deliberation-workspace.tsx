"use client";

import { useState } from "react";
import styles from "./deliberation-workspace.module.css";
import {
  CaseAnalyticsApiClient,
  type QualityChecklistReport,
  type ConsensusDivergenceReport,
  type ExpertPublicGapReport,
  type NormativeModelsReport,
  type IncentiveMapReport,
} from "@/src/lib/case-analytics-api";
import {
  CaseObjectionApiClient,
  type CaseObjectionItem,
  type ObjectionStatus,
} from "@/src/lib/case-objection-api";
import {
  CaseCorrectionApiClient,
  type CaseCorrectionEntry,
  type CorrectionType,
  type CorrectionSeverity,
} from "@/src/lib/case-correction-api";
import { AdminApiError } from "@/src/lib/admin-api";

interface DeliberationWorkspaceProps {
  initialCaseVersionId?: string;
  initialBaseUrl?: string;
  initialCsrfToken?: string;
}

export function DeliberationWorkspace({
  initialCaseVersionId = "22222222-2222-4222-8222-222222222222",
  initialBaseUrl = "http://localhost:8000",
  initialCsrfToken = "",
}: DeliberationWorkspaceProps) {
  const [caseVersionId, setCaseVersionId] = useState(initialCaseVersionId);
  const [baseUrl, setBaseUrl] = useState(initialBaseUrl);
  const [csrfToken, setCsrfToken] = useState(initialCsrfToken);
  const [activeTab, setActiveTab] = useState<"checklist" | "objections" | "corrections" | "analytics">("checklist");

  // Data states
  const [checklist, setChecklist] = useState<QualityChecklistReport | null>(null);
  const [objections, setObjections] = useState<CaseObjectionItem[]>([]);
  const [corrections, setCorrections] = useState<CaseCorrectionEntry[]>([]);
  const [divergence, setDivergence] = useState<ConsensusDivergenceReport | null>(null);
  const [expertGap, setExpertGap] = useState<ExpertPublicGapReport | null>(null);
  const [normative, setNormative] = useState<NormativeModelsReport | null>(null);
  const [incentives, setIncentives] = useState<IncentiveMapReport | null>(null);

  // Status & loading states
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Objection decision form state
  const [selectedObjectionId, setSelectedObjectionId] = useState<string | null>(null);
  const [objectionDecision, setObjectionDecision] = useState<"ACCEPT_AND_FILE_CORRECTION" | "REJECT_WITH_REASON">("ACCEPT_AND_FILE_CORRECTION");
  const [objectionResolutionNote, setObjectionResolutionNote] = useState("");

  // New correction form state
  const [correctionType, setCorrectionType] = useState<CorrectionType>("FACTUAL_UPDATE");
  const [correctionSeverity, setCorrectionSeverity] = useState<CorrectionSeverity>("MINOR");
  const [correctionSummary, setCorrectionSummary] = useState("");
  const [correctionRationale, setCorrectionRationale] = useState("");
  const [correctionPrevText, setCorrectionPrevText] = useState("");
  const [correctionCorrectedText, setCorrectionCorrectedText] = useState("");

  async function loadAllData() {
    if (!caseVersionId.trim()) {
      setStatusMessage({ type: "error", text: "Lütfen geçerli bir Vaka Sürüm Kimliği (Case Version ID) girin." });
      return;
    }

    setLoading(true);
    setStatusMessage(null);

    try {
      const analyticsClient = new CaseAnalyticsApiClient(baseUrl);
      const objectionClient = new CaseObjectionApiClient({ baseUrl, csrfToken });
      const correctionClient = new CaseCorrectionApiClient({ baseUrl, csrfToken });

      const [
        checklistRes,
        objectionsRes,
        correctionsRes,
        divergenceRes,
        expertGapRes,
        normativeRes,
        incentivesRes,
      ] = await Promise.all([
        analyticsClient.getQualityChecklist(caseVersionId),
        objectionClient.listObjections(caseVersionId),
        correctionClient.getCorrectionHistory(caseVersionId),
        analyticsClient.getConsensusDivergence(caseVersionId),
        analyticsClient.getExpertPublicGap(caseVersionId),
        analyticsClient.getNormativeModels(caseVersionId),
        analyticsClient.getIncentiveMap(caseVersionId),
      ]);

      setChecklist(checklistRes);
      setObjections(objectionsRes);
      setCorrections(correctionsRes.corrections);
      setDivergence(divergenceRes);
      setExpertGap(expertGapRes);
      setNormative(normativeRes);
      setIncentives(incentivesRes);

      setStatusMessage({
        type: "success",
        text: `Vaka verileri başarıyla yüklendi: ${checklistRes.criteria.length} kalite kriteri, ${objectionsRes.length} itiraz, ${correctionsRes.corrections.length} düzeltme kaydı.`,
      });
    } catch (err: unknown) {
      const msg = err instanceof AdminApiError ? `[${err.code}] ${err.message}` : String(err);
      setStatusMessage({ type: "error", text: `Veri yüklenirken hata oluştu: ${msg}` });
    } finally {
      setLoading(false);
    }
  }

  async function handleDecideObjection(objectionId: string) {
    if (!csrfToken.trim()) {
      setStatusMessage({ type: "error", text: "İtiraz kararı bildirmek için geçerli bir CSRF token girilmelidir." });
      return;
    }
    if (objectionResolutionNote.trim().length < 10) {
      setStatusMessage({ type: "error", text: "Çözüm/karar gerekçesi en az 10 karakter uzunluğunda olmalıdır." });
      return;
    }

    setLoading(true);
    try {
      const objectionClient = new CaseObjectionApiClient({ baseUrl, csrfToken });
      await objectionClient.decideObjection(caseVersionId, {
        objection_id: objectionId,
        decision: objectionDecision,
        resolution_note: objectionResolutionNote,
        csrf_token: csrfToken,
      });

      setStatusMessage({ type: "success", text: `İtiraz kararı başarıyla kaydedildi (${objectionDecision}).` });
      setSelectedObjectionId(null);
      setObjectionResolutionNote("");

      // Refresh objections
      const refreshed = await objectionClient.listObjections(caseVersionId);
      setObjections(refreshed);
    } catch (err: unknown) {
      const msg = err instanceof AdminApiError ? `[${err.code}] ${err.message}` : String(err);
      setStatusMessage({ type: "error", text: `Karar kaydedilemedi: ${msg}` });
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateCorrection(e: React.FormEvent) {
    e.preventDefault();
    if (!csrfToken.trim()) {
      setStatusMessage({ type: "error", text: "Düzeltme kaydı oluşturmak için geçerli bir CSRF token girilmelidir." });
      return;
    }
    if (correctionSummary.trim().length < 5 || correctionRationale.trim().length < 10) {
      setStatusMessage({ type: "error", text: "Özet en az 5, editoryal gerekçe en az 10 karakter olmalıdır." });
      return;
    }

    setLoading(true);
    try {
      const correctionClient = new CaseCorrectionApiClient({ baseUrl, csrfToken });
      await correctionClient.addCorrection(caseVersionId, {
        correction_type: correctionType,
        severity: correctionSeverity,
        summary: correctionSummary,
        editorial_rationale: correctionRationale,
        previous_value: correctionPrevText.trim() || undefined,
        corrected_value: correctionCorrectedText.trim() || undefined,
        csrf_token: csrfToken,
      });

      setStatusMessage({ type: "success", text: "Yeni editoryal düzeltme kaydı başarıyla oluşturuldu." });
      setCorrectionSummary("");
      setCorrectionRationale("");
      setCorrectionPrevText("");
      setCorrectionCorrectedText("");

      // Refresh corrections
      const refreshed = await correctionClient.getCorrectionHistory(caseVersionId);
      setCorrections(refreshed.corrections);
    } catch (err: unknown) {
      const msg = err instanceof AdminApiError ? `[${err.code}] ${err.message}` : String(err);
      setStatusMessage({ type: "error", text: `Düzeltme kaydedilemedi: ${msg}` });
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className={styles.shell}>
      <header className={styles.hero}>
        <div>
          <p className={styles.eyebrow}>KEFE · Admin Studio · CAP-075 / CAP-068 / CAP-072</p>
          <h1>Deliberation & Quality Audit</h1>
          <p>
            Vaka kalite kontrol kriterleri, halk itirazları yönetimi, şeffaf editoryal düzeltme geçmişi ve
            kolektif uzlaşı analizlerinin bir arada yürütüldüğü denetim çalışma alanı.
          </p>
        </div>
        <aside className={styles.boundary}>
          <strong>Editoryal Tarafsızlık ve Şeffaflık Sınırı</strong>
          <span>
            Vakalar kör ilk (blind-first) ilkesine tabidir. İtirazlar ve düzeltmeler append-only
            kaydedilir; geçmiş kayıtlar asla silinmez veya geriye dönük tahrif edilemez.
          </span>
        </aside>
      </header>

      {/* Control / Filter Bar */}
      <section className={styles.controlBar} aria-label="Bağlantı ve Vaka Parametreleri">
        <div className={styles.controlField}>
          <label htmlFor="case-version-id">Vaka Sürüm Kimliği (UUID)</label>
          <input
            id="case-version-id"
            className={styles.controlInput}
            value={caseVersionId}
            onChange={(e) => setCaseVersionId(e.target.value)}
            placeholder="22222222-2222-4222-8222-222222222222"
          />
        </div>
        <div className={styles.controlField}>
          <label htmlFor="api-base-url">API Base URL</label>
          <input
            id="api-base-url"
            className={styles.controlInput}
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            placeholder="http://localhost:8000"
          />
        </div>
        <div className={styles.controlField}>
          <label htmlFor="csrf-token">CSRF Token (Değişiklikler için)</label>
          <input
            id="csrf-token"
            className={styles.controlInput}
            value={csrfToken}
            onChange={(e) => setCsrfToken(e.target.value)}
            placeholder="Oturum CSRF belirteci"
          />
        </div>
        <button
          type="button"
          className={styles.fetchButton}
          onClick={loadAllData}
          disabled={loading}
        >
          {loading ? "Yükleniyor…" : "Verileri Getir"}
        </button>
      </section>

      {/* Status Message */}
      {statusMessage && (
        <div
          className={`${styles.statusBar} ${
            statusMessage.type === "success" ? styles.statusSuccess : styles.statusError
          }`}
          role="status"
        >
          {statusMessage.text}
        </div>
      )}

      {/* Navigation Tabs */}
      <nav className={styles.tabs} aria-label="Çalışma Alanı Sekmeleri">
        <button
          type="button"
          className={`${styles.tabButton} ${activeTab === "checklist" ? styles.tabActive : ""}`}
          onClick={() => setActiveTab("checklist")}
        >
          Kalite Kontrol Listesi (CAP-075)
        </button>
        <button
          type="button"
          className={`${styles.tabButton} ${activeTab === "objections" ? styles.tabActive : ""}`}
          onClick={() => setActiveTab("objections")}
        >
          Vaka İtirazları (CAP-068) {objections.length > 0 ? `(${objections.length})` : ""}
        </button>
        <button
          type="button"
          className={`${styles.tabButton} ${activeTab === "corrections" ? styles.tabActive : ""}`}
          onClick={() => setActiveTab("corrections")}
        >
          Düzeltme Geçmişi (CAP-072) {corrections.length > 0 ? `(${corrections.length})` : ""}
        </button>
        <button
          type="button"
          className={`${styles.tabButton} ${activeTab === "analytics" ? styles.tabActive : ""}`}
          onClick={() => setActiveTab("analytics")}
        >
          Deliberation Analitikleri (CAP-039 / CAP-041)
        </button>
      </nav>

      {/* Tab 1: Quality Checklist */}
      {activeTab === "checklist" && (
        <section aria-label="Kalite Kontrol Listesi">
          <div className={styles.sectionTitle}>
            <span>8 Boyutlu Vaka Kalite Denetimi</span>
            {checklist && (
              <span
                className={`${styles.badge} ${
                  checklist.overall_status === "PASSED"
                    ? styles.badgePassed
                    : checklist.overall_status === "PROVISIONAL"
                    ? styles.badgeProvisional
                    : styles.badgeFailed
                }`}
              >
                {checklist.overall_status} (Skor: {Math.round(checklist.overall_score * 100)}%)
              </span>
            )}
          </div>

          {checklist ? (
            <div className={styles.criteriaGrid}>
              {checklist.criteria.map((crit) => (
                <div key={crit.code} className={styles.criterionCard}>
                  <div className={styles.criterionHeader}>
                    <span className={styles.criterionName}>{crit.name}</span>
                    <span
                      className={`${styles.badge} ${
                        crit.is_met ? styles.badgePassed : styles.badgeFailed
                      }`}
                    >
                      {crit.is_met ? "SAĞLANDI" : "EKSİK"}
                    </span>
                  </div>
                  <p className={styles.criterionDetails}>{crit.details}</p>
                  <div className={styles.scoreRow}>
                    <span>Skor: {crit.score}</span>
                    <span>·</span>
                    <span>Eşik: {crit.threshold}</span>
                    <span>·</span>
                    <span>Kod: {crit.code}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className={styles.emptyNote}>
              Henüz kalite kontrol verisi yüklenmedi. Yukarıdaki &quot;Verileri Getir&quot; butonuna tıklayın.
            </div>
          )}
        </section>
      )}

      {/* Tab 2: Case Objections */}
      {activeTab === "objections" && (
        <section aria-label="Vaka İtirazları">
          <div className={styles.sectionTitle}>
            <span>Topluluk ve Uzman İtirazları</span>
            <span className={styles.badge}>{objections.length} İtiraz</span>
          </div>

          {objections.length > 0 ? (
            <div className={styles.listContainer}>
              {objections.map((obj) => (
                <div key={obj.objection_id} className={styles.itemCard}>
                  <div className={styles.itemHeader}>
                    <div className={styles.itemMeta}>
                      <span className={styles.itemTitle}>{obj.reason_category}</span>
                      <span className={`${styles.badge} ${obj.status === "SUBMITTED" ? styles.badgeProvisional : styles.badgePassed}`}>
                        {obj.status}
                      </span>
                    </div>
                    <span style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
                      {new Date(obj.created_at).toLocaleString("tr-TR")}
                    </span>
                  </div>
                  <p className={styles.itemStatement}>{obj.statement}</p>
                  {obj.supporting_evidence_url && (
                    <a
                      href={obj.supporting_evidence_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={styles.itemEvidence}
                    >
                      Delil Bağlantısı: {obj.supporting_evidence_url} ↗
                    </a>
                  )}

                  {obj.resolution_note && (
                    <div style={{ fontSize: "0.85rem", color: "var(--muted)", borderLeft: "2px solid var(--gold)", paddingLeft: "0.75rem", marginTop: "0.5rem" }}>
                      <strong>Çözüm Notu:</strong> {obj.resolution_note}
                    </div>
                  )}

                  {obj.status === "SUBMITTED" && (
                    <div className={styles.decisionBox}>
                      {selectedObjectionId === obj.objection_id ? (
                        <div className={styles.actionForm}>
                          <div className={styles.formGrid}>
                            <div className={styles.formField}>
                              <label className={styles.formLabel}>Karar</label>
                              <select
                                className={styles.formSelect}
                                value={objectionDecision}
                                onChange={(e) => setObjectionDecision(e.target.value as "ACCEPT_AND_FILE_CORRECTION" | "REJECT_WITH_REASON")}
                              >
                                <option value="ACCEPT_AND_FILE_CORRECTION">ACCEPT_AND_FILE_CORRECTION (Kabul Et ve Düzeltme Kaydı Aç)</option>
                                <option value="REJECT_WITH_REASON">REJECT_WITH_REASON (Gerekçeli Reddet)</option>
                              </select>
                            </div>
                            <div className={styles.formField}>
                              <label className={styles.formLabel}>Editoryal Gerekçe / Çözüm Notu (Min. 10 krk)</label>
                              <input
                                className={styles.formInput}
                                value={objectionResolutionNote}
                                onChange={(e) => setObjectionResolutionNote(e.target.value)}
                                placeholder="Gerekçeli editoryal açıklama yazın..."
                              />
                            </div>
                          </div>
                          <div style={{ display: "flex", gap: "0.5rem" }}>
                            <button
                              type="button"
                              className={styles.submitBtn}
                              onClick={() => handleDecideObjection(obj.objection_id)}
                              disabled={loading}
                            >
                              Kararı Onayla ve Kaydet
                            </button>
                            <button
                              type="button"
                              style={{ background: "transparent", color: "var(--muted)", border: "1px solid var(--line)", padding: "0.5rem 1rem", borderRadius: "0.4rem", cursor: "pointer" }}
                              onClick={() => setSelectedObjectionId(null)}
                            >
                              İptal
                            </button>
                          </div>
                        </div>
                      ) : (
                        <button
                          type="button"
                          className={styles.submitBtn}
                          onClick={() => {
                            setSelectedObjectionId(obj.objection_id);
                            setObjectionResolutionNote("");
                          }}
                        >
                          İtirazı Değerlendir & Karar Ver
                        </button>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className={styles.emptyNote}>
              Bu vaka için kayıtlı itiraz bulunmuyor veya veriler henüz çekilmedi.
            </div>
          )}
        </section>
      )}

      {/* Tab 3: Correction History */}
      {activeTab === "corrections" && (
        <section aria-label="Düzeltme Geçmişi">
          <div className={styles.sectionTitle}>
            <span>Şeffaf Vaka Düzeltme Kaydı (Changelog)</span>
            <span className={styles.badge}>{corrections.length} Düzeltme</span>
          </div>

          {/* New Correction Form */}
          <div className={styles.itemCard} style={{ marginBottom: "2rem" }}>
            <h3 style={{ margin: "0 0 1rem", fontSize: "1rem", color: "var(--gold)" }}>
              + Yeni Editoryal Düzeltme Ekle
            </h3>
            <form onSubmit={handleCreateCorrection} className={styles.actionForm}>
              <div className={styles.formGrid}>
                <div className={styles.formField}>
                  <label className={styles.formLabel}>Düzeltme Türü</label>
                  <select
                    className={styles.formSelect}
                    value={correctionType}
                    onChange={(e) => setCorrectionType(e.target.value as CorrectionType)}
                  >
                    <option value="FACTUAL_UPDATE">FACTUAL_UPDATE (Olgusal Güncelleme)</option>
                    <option value="CLARIFICATION">CLARIFICATION (Netleştirme)</option>
                    <option value="SOURCE_EXPANSION">SOURCE_EXPANSION (Kaynak Genişletme)</option>
                    <option value="TYPO_FIX">TYPO_FIX (Yazım Düzeltmesi)</option>
                    <option value="LEGAL_STATUS_UPDATE">LEGAL_STATUS_UPDATE (Hukuki Durum Güncellemesi)</option>
                  </select>
                </div>
                <div className={styles.formField}>
                  <label className={styles.formLabel}>Önem Derecesi (Severity)</label>
                  <select
                    className={styles.formSelect}
                    value={correctionSeverity}
                    onChange={(e) => setCorrectionSeverity(e.target.value as CorrectionSeverity)}
                  >
                    <option value="MINOR">MINOR (Küçük)</option>
                    <option value="MATERIAL">MATERIAL (Maddi / Önemli)</option>
                    <option value="SUBSTANTIAL">SUBSTANTIAL (Esaslı)</option>
                  </select>
                </div>
              </div>

              <div className={styles.formField}>
                <label className={styles.formLabel}>Düzeltme Özeti (Min. 5 karakter)</label>
                <input
                  className={styles.formInput}
                  value={correctionSummary}
                  onChange={(e) => setCorrectionSummary(e.target.value)}
                  placeholder="Düzeltilen unsurun kısa açıklaması..."
                  required
                />
              </div>

              <div className={styles.formField}>
                <label className={styles.formLabel}>Editoryal Gerekçe (Min. 10 karakter)</label>
                <textarea
                  className={styles.formTextarea}
                  value={correctionRationale}
                  onChange={(e) => setCorrectionRationale(e.target.value)}
                  placeholder="Bu düzeltmenin neden yapıldığını açıklayan tarafsız gerekçe..."
                  required
                />
              </div>

              <div className={styles.formGrid}>
                <div className={styles.formField}>
                  <label className={styles.formLabel}>Önceki Değer / Metin (İsteğe bağlı)</label>
                  <textarea
                    className={styles.formTextarea}
                    value={correctionPrevText}
                    onChange={(e) => setCorrectionPrevText(e.target.value)}
                    placeholder="Eski metin parçası..."
                  />
                </div>
                <div className={styles.formField}>
                  <label className={styles.formLabel}>Düzeltilmiş Değer / Metin (İsteğe bağlı)</label>
                  <textarea
                    className={styles.formTextarea}
                    value={correctionCorrectedText}
                    onChange={(e) => setCorrectionCorrectedText(e.target.value)}
                    placeholder="Yeni düzeltilmiş metin parçası..."
                  />
                </div>
              </div>

              <button type="submit" className={styles.submitBtn} disabled={loading}>
                {loading ? "Kaydediliyor…" : "Düzeltmeyi Kaydet"}
              </button>
            </form>
          </div>

          {/* Corrections Timeline List */}
          {corrections.length > 0 ? (
            <div className={styles.listContainer}>
              {corrections.map((cor) => (
                <div key={cor.correction_id} className={styles.itemCard}>
                  <div className={styles.itemHeader}>
                    <div className={styles.itemMeta}>
                      <span className={styles.itemTitle}>{cor.summary}</span>
                      <span className={`${styles.badge} ${cor.severity === "SUBSTANTIAL" ? styles.badgeFailed : cor.severity === "MATERIAL" ? styles.badgeProvisional : styles.badgePassed}`}>
                        {cor.severity}
                      </span>
                      <span className={styles.badge}>{cor.correction_type}</span>
                    </div>
                    <span style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
                      {new Date(cor.timestamp).toLocaleString("tr-TR")}
                    </span>
                  </div>
                  <p style={{ fontSize: "0.88rem", color: "var(--muted)", margin: "0 0 0.5rem" }}>
                    <strong>Gerekçe:</strong> {cor.editorial_rationale}
                  </p>
                  {(cor.previous_value || cor.corrected_value) && (
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", background: "var(--background)", padding: "0.75rem", borderRadius: "0.5rem", fontSize: "0.82rem" }}>
                      <div>
                        <span style={{ color: "#e57373", fontWeight: 600 }}>Önceki Metin:</span>
                        <p style={{ margin: "0.25rem 0 0", color: "var(--muted)" }}>{cor.previous_value || "—"}</p>
                      </div>
                      <div>
                        <span style={{ color: "#81c784", fontWeight: 600 }}>Düzeltilmiş Metin:</span>
                        <p style={{ margin: "0.25rem 0 0", color: "var(--text)" }}>{cor.corrected_value || "—"}</p>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className={styles.emptyNote}>
              Bu vaka için kaydedilmiş düzeltme geçmişi bulunmuyor.
            </div>
          )}
        </section>
      )}

      {/* Tab 4: Deliberation Analytics */}
      {activeTab === "analytics" && (
        <section aria-label="Kolektif Analitikler">
          <div className={styles.sectionTitle}>
            <span>Kolektif Dağılım, Değer Ayrışması ve Normatif Modeller</span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.25rem" }}>
            {/* Divergence */}
            <div className={styles.itemCard}>
              <h3 style={{ margin: "0 0 0.5rem", fontSize: "1rem", color: "var(--gold)" }}>
                {divergence ? divergence.label_tr : "Uzlaşı / Ayrışma Dağılımı"}
              </h3>
              {divergence ? (
                <div>
                  <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginBottom: "0.5rem" }}>
                    <span className={`${styles.badge} ${styles.badgePassed}`}>{divergence.classification}</span>
                    <span style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
                      Öncü Pay: {Math.round(divergence.leading_share * 100)}% · Ayrışma Marjı: {Math.round(divergence.margin_of_divergence * 100)}%
                    </span>
                  </div>
                  <p style={{ fontSize: "0.85rem", color: "var(--muted)", margin: 0 }}>
                    {divergence.description_tr}
                  </p>
                </div>
              ) : (
                <p style={{ fontSize: "0.85rem", color: "var(--muted)" }}>Veri yüklenmedi.</p>
              )}
            </div>

            {/* Expert Public Gap */}
            <div className={styles.itemCard}>
              <h3 style={{ margin: "0 0 0.5rem", fontSize: "1rem", color: "var(--gold)" }}>
                Uzman - Yurttaş Epistemik Boşluğu (CAP-041)
              </h3>
              {expertGap ? (
                <div>
                  <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginBottom: "0.5rem" }}>
                    <span className={`${styles.badge} ${styles.badgeProvisional}`}>{expertGap.gap_classification}</span>
                    <span style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
                      Boşluk Skoru: {expertGap.gap_score}
                    </span>
                  </div>
                  <div style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
                    <strong>Sürtüşme Noktaları:</strong> {expertGap.friction_points.join(", ")}
                  </div>
                </div>
              ) : (
                <p style={{ fontSize: "0.85rem", color: "var(--muted)" }}>Veri yüklenmedi.</p>
              )}
            </div>
          </div>

          {/* Normative Models */}
          <div className={styles.itemCard} style={{ marginTop: "1.25rem" }}>
            <h3 style={{ margin: "0 0 0.75rem", fontSize: "1rem", color: "var(--gold)" }}>
              Normatif Felsefi Değerlendirme (CAP-019)
            </h3>
            {normative ? (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "1rem" }}>
                {normative.evaluations.map((ev) => (
                  <div key={ev.option_code} style={{ background: "var(--background)", padding: "1rem", borderRadius: "0.5rem", border: "1px solid var(--line)" }}>
                    <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--text)", marginBottom: "0.35rem" }}>
                      Seçenek {ev.option_code}: {ev.dominant_philosophy}
                    </div>
                    <div style={{ fontSize: "0.8rem", color: "var(--muted)", display: "flex", flexDirection: "column", gap: "0.2rem" }}>
                      <span>Fayda (Utilitarian): {ev.utilitarian_score}</span>
                      <span>Ödev/Hak (Deontological): {ev.deontological_score}</span>
                      <span>Rawlsian Adalet: {ev.rawlsian_score}</span>
                      <span>Erdem Etiği: {ev.virtue_score}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ fontSize: "0.85rem", color: "var(--muted)" }}>Veri yüklenmedi.</p>
            )}
          </div>
        </section>
      )}
    </main>
  );
}
