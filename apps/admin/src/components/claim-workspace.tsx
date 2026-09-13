"use client";

import { useState } from "react";
import styles from "./claim-workspace.module.css";
import {
  ClaimApiClient,
  ClaimApiError,
  type ClaimItem,
  type ClaimType,
  type ClaimState,
  type ReviewState,
  type ArgumentRelationKind,
} from "@/src/lib/claim-api";

interface ClaimWorkspaceProps {
  initialBaseUrl?: string;
  initialCsrfToken?: string;
}

export function ClaimWorkspace({
  initialBaseUrl = "http://localhost:8000",
  initialCsrfToken = "",
}: ClaimWorkspaceProps) {
  const [baseUrl, setBaseUrl] = useState(initialBaseUrl);
  const [csrfToken, setCsrfToken] = useState(initialCsrfToken);
  const [activeTab, setActiveTab] = useState<"claims" | "assessments" | "assertions" | "graph">("claims");

  // Loaded claim
  const [claimSearchId, setClaimSearchId] = useState("");
  const [activeClaim, setActiveClaim] = useState<ClaimItem | null>(null);
  const [recentClaims, setRecentClaims] = useState<ClaimItem[]>([]);

  // Form states - Create Claim
  const [newClaimText, setNewClaimText] = useState("");
  const [newClaimLang, setNewClaimLang] = useState("tr");

  // Form states - Add Assessment
  const [assessmentType, setAssessmentType] = useState<ClaimType>("FACTUAL");
  const [assessmentState, setAssessmentState] = useState<ClaimState>("CLAIMED");
  const [assessmentReviewState, setAssessmentReviewState] = useState<ReviewState>("ACCEPTED");
  const [assessmentReviewer, setAssessmentReviewer] = useState("editor:admin");
  const [assessmentRationale, setAssessmentRationale] = useState("");

  // Form states - Add Assertion
  const [claimantKind, setClaimantKind] = useState("CIVIL_SOCIETY");
  const [claimantRef, setClaimantRef] = useState("");
  const [assertionProvenance, setAssertionProvenance] = useState("");

  // Form states - Graph & Arguments
  const [targetClaimId, setTargetClaimId] = useState("");
  const [claimRelationCode, setClaimRelationCode] = useState("NARROWS_SCOPE_OF");
  const [argumentBody, setArgumentBody] = useState("");
  const [argumentRelation, setArgumentRelation] = useState<ArgumentRelationKind>("SUPPORTS");

  // UI state
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  function getClient(): ClaimApiClient {
    return new ClaimApiClient({ baseUrl, csrfToken });
  }

  async function handleLoadClaim(idToLoad?: string) {
    const id = (idToLoad ?? claimSearchId).trim();
    if (!id) {
      setStatusMessage({ type: "error", text: "Lütfen geçerli bir İddia Kimliği (UUID) girin." });
      return;
    }
    setLoading(true);
    setStatusMessage(null);
    try {
      const client = getClient();
      const claim = await client.getClaim(id);
      setActiveClaim(claim);
      setClaimSearchId(claim.id);
      setStatusMessage({ type: "success", text: `İddia başarıyla yüklendi: ${claim.id}` });
    } catch (err) {
      const msg = err instanceof ClaimApiError ? `[${err.code}] ${err.message}` : "İddia yüklenemedi.";
      setStatusMessage({ type: "error", text: msg });
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateClaim(e: React.FormEvent) {
    e.preventDefault();
    if (!newClaimText.trim() || newClaimText.trim().length < 3) {
      setStatusMessage({ type: "error", text: "İddia metni en az 3 karakter olmalıdır." });
      return;
    }
    setLoading(true);
    setStatusMessage(null);
    try {
      const client = getClient();
      const created = await client.createClaim({
        normalized_text: newClaimText.trim(),
        language_code: newClaimLang.trim(),
      });
      setActiveClaim(created);
      setClaimSearchId(created.id);
      setRecentClaims((prev) => [created, ...prev.filter((c) => c.id !== created.id)]);
      setNewClaimText("");
      setStatusMessage({ type: "success", text: `Yeni iddia oluşturuldu: ${created.id}` });
    } catch (err) {
      const msg = err instanceof ClaimApiError ? `[${err.code}] ${err.message}` : "İddia oluşturulamadı.";
      setStatusMessage({ type: "error", text: msg });
    } finally {
      setLoading(false);
    }
  }

  async function handleAddAssessment(e: React.FormEvent) {
    e.preventDefault();
    if (!activeClaim) {
      setStatusMessage({ type: "error", text: "Önce değerlendirilecek bir iddia seçin veya yükleyin." });
      return;
    }
    setLoading(true);
    setStatusMessage(null);
    try {
      const client = getClient();
      await client.addClaimAssessment(activeClaim.id, {
        claim_type: assessmentType,
        claim_state: assessmentState,
        review_state: assessmentReviewState,
        reviewer_ref: assessmentReviewer.trim() || undefined,
        rationale_code: assessmentRationale.trim() || undefined,
      });
      await handleLoadClaim(activeClaim.id);
      setStatusMessage({ type: "success", text: "İddia değerlendirmesi (assessment) başarıyla eklendi." });
      setAssessmentRationale("");
    } catch (err) {
      const msg = err instanceof ClaimApiError ? `[${err.code}] ${err.message}` : "Değerlendirme eklenemedi.";
      setStatusMessage({ type: "error", text: msg });
    } finally {
      setLoading(false);
    }
  }

  async function handleAddAssertion(e: React.FormEvent) {
    e.preventDefault();
    if (!activeClaim) {
      setStatusMessage({ type: "error", text: "Önce bir iddia seçin veya yükleyin." });
      return;
    }
    if (!claimantRef.trim()) {
      setStatusMessage({ type: "error", text: "Lütfen aktör referansı belirtin." });
      return;
    }
    setLoading(true);
    setStatusMessage(null);
    try {
      const client = getClient();
      await client.addClaimAssertion(activeClaim.id, {
        claimant_kind: claimantKind,
        claimant_ref: claimantRef.trim(),
        provenance_ref: assertionProvenance.trim() || undefined,
      });
      await handleLoadClaim(activeClaim.id);
      setStatusMessage({ type: "success", text: "Aktör beyanı (assertion) başarıyla bağlandı." });
      setClaimantRef("");
      setAssertionProvenance("");
    } catch (err) {
      const msg = err instanceof ClaimApiError ? `[${err.code}] ${err.message}` : "Beyan eklenemedi.";
      setStatusMessage({ type: "error", text: msg });
    } finally {
      setLoading(false);
    }
  }

  async function handleAddClaimRelation(e: React.FormEvent) {
    e.preventDefault();
    if (!activeClaim) {
      setStatusMessage({ type: "error", text: "Önce kaynak iddiayı seçin." });
      return;
    }
    if (!targetClaimId.trim()) {
      setStatusMessage({ type: "error", text: "Hedef iddia kimliğini (UUID) belirtin." });
      return;
    }
    setLoading(true);
    setStatusMessage(null);
    try {
      const client = getClient();
      await client.addClaimRelation(activeClaim.id, {
        to_claim_id: targetClaimId.trim(),
        relation_code: claimRelationCode.trim(),
        review_state: "ACCEPTED",
      });
      await handleLoadClaim(activeClaim.id);
      setStatusMessage({ type: "success", text: "İddia ilişkisi grafiğe eklendi." });
      setTargetClaimId("");
    } catch (err) {
      const msg = err instanceof ClaimApiError ? `[${err.code}] ${err.message}` : "İlişki eklenemedi.";
      setStatusMessage({ type: "error", text: msg });
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateAndLinkArgument(e: React.FormEvent) {
    e.preventDefault();
    if (!activeClaim) {
      setStatusMessage({ type: "error", text: "Önce hedeflenecek iddiayı seçin." });
      return;
    }
    if (!argumentBody.trim() || argumentBody.trim().length < 3) {
      setStatusMessage({ type: "error", text: "Argüman metni en az 3 karakter olmalıdır." });
      return;
    }
    setLoading(true);
    setStatusMessage(null);
    try {
      const client = getClient();
      const arg = await client.createArgument({
        body: argumentBody.trim(),
        review_state: "ACCEPTED",
      });
      await client.addArgumentRelation(arg.id, {
        target_kind: "CLAIM",
        target_ref: activeClaim.id,
        relation: argumentRelation,
        review_state: "ACCEPTED",
      });
      await handleLoadClaim(activeClaim.id);
      setStatusMessage({ type: "success", text: `Argüman (${arg.id}) oluşturuldu ve iddiaya bağlandı.` });
      setArgumentBody("");
    } catch (err) {
      const msg = err instanceof ClaimApiError ? `[${err.code}] ${err.message}` : "Argüman eklenemedi.";
      setStatusMessage({ type: "error", text: msg });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.shell}>
      {/* 2-Column Hero & Boundary */}
      <section className={styles.hero} aria-label="İddia ve Graf Yönetimi Tanıtımı">
        <div>
          <div className={styles.eyebrow}>CAP-057 / CAP-058 / CAP-059 · BİLGİ VE İDDİA GRAFİĞİ</div>
          <h1>İddia ve Argüman Grafiği Yönetimi</h1>
          <p>
            Birinci sınıf iddia sınıflandırması (CAP-057), append-only kanıt değerlendirme döngüsü (CAP-058) ve çok-taraflı argüman ağ ilişkilerini (CAP-059) yönetin.
          </p>
        </div>
        <div className={styles.boundary}>
          <strong>Editoryal Bilgi Sınırı (Knowledge Boundary)</strong>
          <span>
            İddialar ve değerlendirmeler salt-eklenir (append-only) mimaridedir. Ham kullanıcı kararları değiştirilemez; kanıt ve iddia ilişkileri açık editoryal denetime tabidir.
          </span>
        </div>
      </section>

      {/* Control Bar */}
      <section className={styles.controlBar} aria-label="API Bağlantı ve İddia Seçimi">
        <div className={styles.controlField}>
          <label htmlFor="claim-base-url">API Base URL</label>
          <input
            id="claim-base-url"
            type="text"
            className={styles.controlInput}
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
          />
        </div>
        <div className={styles.controlField}>
          <label htmlFor="claim-csrf-token">CSRF Token</label>
          <input
            id="claim-csrf-token"
            type="password"
            className={styles.controlInput}
            placeholder="CSRF Belirteci"
            value={csrfToken}
            onChange={(e) => setCsrfToken(e.target.value)}
          />
        </div>
        <div className={styles.controlField}>
          <label htmlFor="claim-search-id">İddia Kimliği (UUID)</label>
          <input
            id="claim-search-id"
            type="text"
            className={styles.controlInput}
            placeholder="İddia UUID girin..."
            value={claimSearchId}
            onChange={(e) => setClaimSearchId(e.target.value)}
          />
        </div>
        <button
          type="button"
          className={styles.loadBtn}
          onClick={() => handleLoadClaim()}
          disabled={loading || !claimSearchId.trim()}
        >
          {loading ? "Yükleniyor..." : "İddiayı Getir"}
        </button>
      </section>

      {/* Status feedback */}
      {statusMessage && (
        <div
          role="status"
          className={`${styles.statusBanner} ${
            statusMessage.type === "success" ? styles.statusSuccess : styles.statusError
          }`}
        >
          {statusMessage.type === "success" ? "✓" : "⚠"} {statusMessage.text}
        </div>
      )}

      {/* Tabs */}
      <div className={styles.tabs} role="tablist">
        <button
          role="tab"
          type="button"
          aria-selected={activeTab === "claims"}
          className={`${styles.tabBtn} ${activeTab === "claims" ? styles.tabBtnActive : ""}`}
          onClick={() => setActiveTab("claims")}
        >
          1. İddia Kataloğu & Oluşturma (CAP-057)
        </button>
        <button
          role="tab"
          type="button"
          aria-selected={activeTab === "assessments"}
          className={`${styles.tabBtn} ${activeTab === "assessments" ? styles.tabBtnActive : ""}`}
          onClick={() => setActiveTab("assessments")}
        >
          2. Değerlendirme & Kanıt Döngüsü (CAP-058)
        </button>
        <button
          role="tab"
          type="button"
          aria-selected={activeTab === "assertions"}
          className={`${styles.tabBtn} ${activeTab === "assertions" ? styles.tabBtnActive : ""}`}
          onClick={() => setActiveTab("assertions")}
        >
          3. Aktör Beyanları (Assertions)
        </button>
        <button
          role="tab"
          type="button"
          aria-selected={activeTab === "graph"}
          className={`${styles.tabBtn} ${activeTab === "graph" ? styles.tabBtnActive : ""}`}
          onClick={() => setActiveTab("graph")}
        >
          4. Argüman & Bilgi Grafı (CAP-059)
        </button>
      </div>

      {/* Active Claim Banner if loaded */}
      {activeClaim && (
        <div className={styles.contentCard} style={{ borderColor: "var(--gold)" }}>
          <div className={styles.cardHeader}>
            <h3>Seçili İddia: {activeClaim.id}</h3>
            <span className={styles.badge} style={{ background: "rgba(201, 168, 76, 0.2)", color: "var(--gold)" }}>
              Dil: {activeClaim.language_code.toUpperCase()}
            </span>
          </div>
          <p style={{ fontSize: "1.05rem", color: "var(--text)", fontWeight: 600, margin: "0 0 0.5rem" }}>
            “{activeClaim.normalized_text}”
          </p>
          <div className={styles.listItemMeta}>
            <span>Oluşturulma: {new Date(activeClaim.created_at).toLocaleString("tr-TR")}</span>
            <span>Değerlendirme: {activeClaim.assessments?.length ?? 0}</span>
            <span>Beyan: {activeClaim.assertions?.length ?? 0}</span>
            <span>İlişki: {activeClaim.relations?.length ?? 0}</span>
          </div>
        </div>
      )}

      {/* Tab 1: Claims */}
      {activeTab === "claims" && (
        <div className={styles.contentCard}>
          <div className={styles.cardHeader}>
            <h3>Yeni Birinci Sınıf İddia (Claim) Oluştur</h3>
          </div>
          <form onSubmit={handleCreateClaim}>
            <div className={styles.formGrid}>
              <div className={styles.formFull}>
                <label htmlFor="new-claim-text">Normalize Edilmiş İddia Metni</label>
                <textarea
                  id="new-claim-text"
                  className={styles.formTextarea}
                  placeholder="Doğrulanabilir veya normatif iddia ifadesini girin..."
                  value={newClaimText}
                  onChange={(e) => setNewClaimText(e.target.value)}
                  required
                />
              </div>
              <div>
                <label htmlFor="new-claim-lang">Dil Kodu</label>
                <input
                  id="new-claim-lang"
                  type="text"
                  className={styles.formInput}
                  value={newClaimLang}
                  onChange={(e) => setNewClaimLang(e.target.value)}
                />
              </div>
              <div style={{ display: "flex", alignItems: "flex-end" }}>
                <button type="submit" className={styles.submitBtn} disabled={loading || !newClaimText.trim()}>
                  {loading ? "Kaydediliyor..." : "İddiayı Kaydet (CAP-057)"}
                </button>
              </div>
            </div>
          </form>

          {recentClaims.length > 0 && (
            <div style={{ marginTop: "2rem" }}>
              <h4 style={{ color: "var(--text)", marginBottom: "0.75rem" }}>Bu Oturumda Eklenen İddialar</h4>
              <div className={styles.listGroup}>
                {recentClaims.map((c) => (
                  <div key={c.id} className={styles.listItem}>
                    <div className={styles.listItemHeader}>
                      <span className={styles.listItemTitle}>{c.normalized_text}</span>
                      <button
                        type="button"
                        className={styles.submitBtn}
                        style={{ padding: "0.3rem 0.75rem", fontSize: "0.75rem" }}
                        onClick={() => handleLoadClaim(c.id)}
                      >
                        Seç ve İncele →
                      </button>
                    </div>
                    <div className={styles.listItemMeta}>
                      <span>UUID: {c.id}</span>
                      <span>Dil: {c.language_code}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Assessments */}
      {activeTab === "assessments" && (
        <div className={styles.contentCard}>
          <div className={styles.cardHeader}>
            <h3>Append-Only Kanıt ve Doğruluk Değerlendirmesi (CAP-058)</h3>
          </div>
          {!activeClaim ? (
            <div className={styles.emptyState}>
              Değerlendirme eklemek veya geçmişi görmek için lütfen önce bir iddia seçin.
            </div>
          ) : (
            <>
              <form onSubmit={handleAddAssessment} style={{ marginBottom: "2rem" }}>
                <div className={styles.formGrid}>
                  <div>
                    <label htmlFor="assessment-type">İddia Taksonomi Türü (Claim Type)</label>
                    <select
                      id="assessment-type"
                      className={styles.formSelect}
                      value={assessmentType}
                      onChange={(e) => setAssessmentType(e.target.value as ClaimType)}
                    >
                      <option value="FACTUAL">FACTUAL (Olgusal)</option>
                      <option value="NORMATIVE">NORMATIVE (Kural/Normatif)</option>
                      <option value="VALUE">VALUE (Değer Yargısı)</option>
                      <option value="CAUSAL">CAUSAL (Nedensel İlişki)</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="assessment-state">İddia Durumu (Claim State)</label>
                    <select
                      id="assessment-state"
                      className={styles.formSelect}
                      value={assessmentState}
                      onChange={(e) => setAssessmentState(e.target.value as ClaimState)}
                    >
                      <option value="CLAIMED">CLAIMED (Yalnızca İddia Edilmiş)</option>
                      <option value="SUPPORTED">SUPPORTED (Kanıtlarla Desteklenmiş)</option>
                      <option value="CONTESTED">CONTESTED (Tartışmalı / Çelişkili)</option>
                      <option value="REFUTED">REFUTED (Çürütülmüş)</option>
                      <option value="UNVERIFIABLE">UNVERIFIABLE (Doğrulanamaz)</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="assessment-reviewer">Denetçi Referansı</label>
                    <input
                      id="assessment-reviewer"
                      type="text"
                      className={styles.formInput}
                      value={assessmentReviewer}
                      onChange={(e) => setAssessmentReviewer(e.target.value)}
                    />
                  </div>
                  <div>
                    <label htmlFor="assessment-rationale">Gerekçe Kodu / Açıklama</label>
                    <input
                      id="assessment-rationale"
                      type="text"
                      className={styles.formInput}
                      placeholder="örn. EVIDENCE_CONFIRMED"
                      value={assessmentRationale}
                      onChange={(e) => setAssessmentRationale(e.target.value)}
                    />
                  </div>
                  <div className={styles.formFull}>
                    <button type="submit" className={styles.submitBtn} disabled={loading}>
                      {loading ? "Ekleniyor..." : "Yeni Değerlendirme Ekle (Append-Only)"}
                    </button>
                  </div>
                </div>
              </form>

              <h4 style={{ color: "var(--text)", marginBottom: "0.75rem" }}>Değerlendirme Yaşam Döngüsü Geçmişi</h4>
              {(!activeClaim.assessments || activeClaim.assessments.length === 0) ? (
                <div className={styles.emptyState}>Bu iddiaya ait henüz bir değerlendirme kaydı yok.</div>
              ) : (
                <div className={styles.listGroup}>
                  {activeClaim.assessments.map((a) => (
                    <div key={a.id} className={styles.listItem}>
                      <div className={styles.listItemHeader}>
                        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                          <span
                            className={`${styles.badge} ${
                              a.claim_type === "FACTUAL"
                                ? styles.badgeFactual
                                : a.claim_type === "NORMATIVE"
                                ? styles.badgeNormative
                                : a.claim_type === "VALUE"
                                ? styles.badgeValue
                                : styles.badgeCausal
                            }`}
                          >
                            {a.claim_type}
                          </span>
                          <span
                            className={`${styles.badge} ${
                              a.claim_state === "SUPPORTED"
                                ? styles.badgeSupported
                                : a.claim_state === "CONTESTED"
                                ? styles.badgeContested
                                : a.claim_state === "REFUTED"
                                ? styles.badgeRefuted
                                : styles.badgeClaimed
                            }`}
                          >
                            {a.claim_state}
                          </span>
                        </div>
                        <span style={{ fontSize: "0.78rem", color: "var(--muted)" }}>
                          {new Date(a.assessed_at).toLocaleString("tr-TR")}
                        </span>
                      </div>
                      <div className={styles.listItemMeta}>
                        <span>Denetçi: {a.reviewer_ref ?? "Bilinmiyor"}</span>
                        <span>Taksonomi: {a.taxonomy_version}</span>
                        <span>İnceleme: {a.review_state}</span>
                        {a.rationale_code && <span>Gerekçe: {a.rationale_code}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Tab 3: Assertions */}
      {activeTab === "assertions" && (
        <div className={styles.contentCard}>
          <div className={styles.cardHeader}>
            <h3>Aktör ve Kaynak Beyanları (Assertions)</h3>
          </div>
          {!activeClaim ? (
            <div className={styles.emptyState}>Lütfen önce bir iddia seçin.</div>
          ) : (
            <>
              <form onSubmit={handleAddAssertion} style={{ marginBottom: "2rem" }}>
                <div className={styles.formGrid}>
                  <div>
                    <label htmlFor="claimant-kind">Aktör / Kaynak Türü</label>
                    <select
                      id="claimant-kind"
                      className={styles.formSelect}
                      value={claimantKind}
                      onChange={(e) => setClaimantKind(e.target.value)}
                    >
                      <option value="CIVIL_SOCIETY">CIVIL_SOCIETY (Sivil Toplum)</option>
                      <option value="ACADEMIC">ACADEMIC (Akademik Araştırma)</option>
                      <option value="OFFICIAL">OFFICIAL (Resmi Kurum)</option>
                      <option value="MEDIA">MEDIA (Bağımsız Medya)</option>
                      <option value="INDIVIDUAL">INDIVIDUAL (Bireysel Beyan)</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="claimant-ref">Aktör Referansı</label>
                    <input
                      id="claimant-ref"
                      type="text"
                      className={styles.formInput}
                      placeholder="örn. ngo:environmental-justice"
                      value={claimantRef}
                      onChange={(e) => setClaimantRef(e.target.value)}
                      required
                    />
                  </div>
                  <div className={styles.formFull}>
                    <label htmlFor="assertion-prov">Kaynak Belge / Kanıt Referansı</label>
                    <input
                      id="assertion-prov"
                      type="text"
                      className={styles.formInput}
                      placeholder="örn. brief-doc-2026-09"
                      value={assertionProvenance}
                      onChange={(e) => setAssertionProvenance(e.target.value)}
                    />
                  </div>
                  <div className={styles.formFull}>
                    <button type="submit" className={styles.submitBtn} disabled={loading || !claimantRef.trim()}>
                      {loading ? "Ekleniyor..." : "Beyanı Kaydet"}
                    </button>
                  </div>
                </div>
              </form>

              <h4 style={{ color: "var(--text)", marginBottom: "0.75rem" }}>Kayıtlı Aktör Beyanları</h4>
              {(!activeClaim.assertions || activeClaim.assertions.length === 0) ? (
                <div className={styles.emptyState}>Bu iddiaya bağlanmış aktör beyanı bulunamadı.</div>
              ) : (
                <div className={styles.listGroup}>
                  {activeClaim.assertions.map((ast) => (
                    <div key={ast.id} className={styles.listItem}>
                      <div className={styles.listItemHeader}>
                        <span className={styles.listItemTitle}>{ast.claimant_ref}</span>
                        <span className={styles.badge} style={{ background: "rgba(255,255,255,0.1)", color: "#fff" }}>
                          {ast.claimant_kind}
                        </span>
                      </div>
                      <div className={styles.listItemMeta}>
                        <span>Zaman: {new Date(ast.asserted_at).toLocaleString("tr-TR")}</span>
                        {ast.provenance_ref && <span>Kaynak: {ast.provenance_ref}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Tab 4: Graph & Arguments */}
      {activeTab === "graph" && (
        <div className={styles.contentCard}>
          <div className={styles.cardHeader}>
            <h3>İddia ve Argüman Ağ İlişkileri Grafı (CAP-059)</h3>
          </div>
          {!activeClaim ? (
            <div className={styles.emptyState}>Graf ilişkilerini yönetmek için lütfen önce bir iddia seçin.</div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
              {/* Left Column: Claim Relations */}
              <div>
                <h4 style={{ color: "var(--text)", marginBottom: "0.75rem" }}>İddia-İddia İlişkisi Ekle</h4>
                <form onSubmit={handleAddClaimRelation} style={{ marginBottom: "1.5rem" }}>
                  <div className={styles.formFull} style={{ marginBottom: "0.75rem" }}>
                    <label htmlFor="target-claim-id">Hedef İddia Kimliği (To Claim ID)</label>
                    <input
                      id="target-claim-id"
                      type="text"
                      className={styles.formInput}
                      placeholder="Hedef Claim UUID..."
                      value={targetClaimId}
                      onChange={(e) => setTargetClaimId(e.target.value)}
                      required
                    />
                  </div>
                  <div className={styles.formFull} style={{ marginBottom: "1rem" }}>
                    <label htmlFor="claim-relation-code">İlişki Kodu</label>
                    <select
                      id="claim-relation-code"
                      className={styles.formSelect}
                      value={claimRelationCode}
                      onChange={(e) => setClaimRelationCode(e.target.value)}
                    >
                      <option value="NARROWS_SCOPE_OF">NARROWS_SCOPE_OF (Kapsamı Daraltır)</option>
                      <option value="BROADENS_SCOPE_OF">BROADENS_SCOPE_OF (Kapsamı Genişletir)</option>
                      <option value="CONTRADICTS">CONTRADICTS (Çelişir)</option>
                      <option value="DEPENDS_ON">DEPENDS_ON (Bağımlıdır)</option>
                    </select>
                  </div>
                  <button type="submit" className={styles.submitBtn} disabled={loading || !targetClaimId.trim()}>
                    {loading ? "Bağlanıyor..." : "İddiaları Bağla"}
                  </button>
                </form>

                <h5 style={{ color: "var(--muted)", marginBottom: "0.5rem" }}>Mevcut İddia İlişkileri</h5>
                {(!activeClaim.relations || activeClaim.relations.length === 0) ? (
                  <div className={styles.emptyState} style={{ padding: "1rem" }}>Bağlı iddia ilişkisi yok.</div>
                ) : (
                  <div className={styles.listGroup}>
                    {activeClaim.relations.map((r) => (
                      <div key={r.id} className={styles.listItem}>
                        <span className={styles.listItemTitle}>{r.relation_code}</span>
                        <div className={styles.listItemMeta}>
                          <span>Kimden: {r.from_claim_id.slice(0, 8)}...</span>
                          <span>Kime: {r.to_claim_id.slice(0, 8)}...</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Right Column: Argument-to-Claim relations */}
              <div>
                <h4 style={{ color: "var(--text)", marginBottom: "0.75rem" }}>Yeni Argüman Oluştur & Bağla</h4>
                <form onSubmit={handleCreateAndLinkArgument} style={{ marginBottom: "1.5rem" }}>
                  <div className={styles.formFull} style={{ marginBottom: "0.75rem" }}>
                    <label htmlFor="argument-body">Argüman İfadesi</label>
                    <textarea
                      id="argument-body"
                      className={styles.formTextarea}
                      placeholder="İddiayı destekleyen, çürüten veya niteleyen argüman..."
                      value={argumentBody}
                      onChange={(e) => setArgumentBody(e.target.value)}
                      required
                    />
                  </div>
                  <div className={styles.formFull} style={{ marginBottom: "1rem" }}>
                    <label htmlFor="argument-relation">Argüman İlişkisi (Relation)</label>
                    <select
                      id="argument-relation"
                      className={styles.formSelect}
                      value={argumentRelation}
                      onChange={(e) => setArgumentRelation(e.target.value as ArgumentRelationKind)}
                    >
                      <option value="SUPPORTS">SUPPORTS (Destekler)</option>
                      <option value="ATTACKS">ATTACKS (Saldırır)</option>
                      <option value="REBUTS">REBUTS (Çürütür)</option>
                      <option value="QUALIFIES">QUALIFIES (Nitelendirir/Sınırlar)</option>
                      <option value="UNDERCUTS">UNDERCUTS (Dayanağı Zayıflatır)</option>
                    </select>
                  </div>
                  <button type="submit" className={styles.submitBtn} disabled={loading || !argumentBody.trim()}>
                    {loading ? "Kaydediliyor..." : "Argümanı Grafiğe Ekle"}
                  </button>
                </form>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
