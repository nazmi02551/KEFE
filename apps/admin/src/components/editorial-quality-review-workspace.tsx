"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import styles from "@/src/components/editorial-quality-review-workspace.module.css";
import { AdminApiClient, AdminApiError } from "@/src/lib/admin-api";
import {
  approvalRequest,
  canApproveEditorialReview,
  canRejectEditorialReview,
  rejectionRequest
} from "@/src/lib/editorial-quality-review";
import type {
  AdminSession,
  AuthoringAuditEntry,
  EditorialReviewDetail,
  EditorialReviewQueueItem
} from "@/src/lib/contracts";

function messageFor(error: unknown): string {
  if (error instanceof AdminApiError) return `${error.code}: ${error.message}`;
  if (error instanceof Error) return error.message.slice(0, 500);
  return "Beklenmeyen bir hata oluştu.";
}

function formattedDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString("tr-TR");
}

function pretty(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

export function EditorialQualityReviewWorkspace() {
  const configuredBase = process.env.NEXT_PUBLIC_KEFE_API_BASE_URL ?? "";
  const [apiBaseUrl, setApiBaseUrl] = useState(configuredBase);
  const [csrfToken, setCsrfToken] = useState("");
  const [session, setSession] = useState<AdminSession | null>(null);
  const [contentRisk, setContentRisk] = useState("");
  const [primaryDomain, setPrimaryDomain] = useState("");
  const [limit, setLimit] = useState(25);
  const [offset, setOffset] = useState(0);
  const [nextOffset, setNextOffset] = useState<number | null>(null);
  const [queue, setQueue] = useState<EditorialReviewQueueItem[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState("");
  const [detail, setDetail] = useState<EditorialReviewDetail | null>(null);
  const [completedModes, setCompletedModes] = useState<string[]>([]);
  const [approveConfirmed, setApproveConfirmed] = useState(false);
  const [rejectRationale, setRejectRationale] = useState("");
  const [audit, setAudit] = useState<AuthoringAuditEntry[]>([]);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState("");

  const client = useMemo(
    () => () => new AdminApiClient({ baseUrl: apiBaseUrl, csrfToken }),
    [apiBaseUrl, csrfToken]
  );

  async function execute(action: () => Promise<void>) {
    setBusy(true);
    setFeedback("");
    try {
      await action();
    } catch (error) {
      setFeedback(messageFor(error));
    } finally {
      setBusy(false);
    }
  }

  async function verifySession() {
    await execute(async () => {
      const resolved = await client().session();
      setSession(resolved);
      setFeedback("Reviewer oturumu açık komutla doğrulandı.");
    });
  }

  async function loadQueue(targetOffset = 0) {
    await execute(async () => {
      const page = await client().contentReviews({
        limit,
        offset: targetOffset,
        content_risk: contentRisk.trim() || undefined,
        primary_domain_code: primaryDomain.trim() || undefined
      });
      setQueue(page.items);
      setOffset(targetOffset);
      setNextOffset(page.next_offset);
      setSelectedVersionId("");
      setDetail(null);
      setAudit([]);
      setCompletedModes([]);
      setApproveConfirmed(false);
      setRejectRationale("");
      setFeedback(`${page.items.length} IN_REVIEW CaseVersion yüklendi.`);
    });
  }

  function selectItem(versionId: string) {
    setSelectedVersionId(versionId);
    setDetail(null);
    setAudit([]);
    setCompletedModes([]);
    setApproveConfirmed(false);
    setRejectRationale("");
    setFeedback("Seçim yapıldı. Ayrıntı henüz yüklenmedi.");
  }

  async function loadDetail() {
    if (!selectedVersionId) {
      setFeedback("Önce kuyruktan bir CaseVersion seçin.");
      return;
    }
    await execute(async () => {
      const loaded = await client().contentReview(selectedVersionId);
      setDetail(loaded);
      setCompletedModes([]);
      setApproveConfirmed(false);
      setRejectRationale("");
      setAudit([]);
      setFeedback("Salt okunur inceleme ayrıntısı açık komutla yüklendi.");
    });
  }

  async function loadAudit() {
    if (!detail) {
      setFeedback("Önce inceleme ayrıntısını yükleyin.");
      return;
    }
    await execute(async () => {
      const trail = await client().caseAudit(detail.version.case_id);
      setAudit(trail.items);
      setFeedback(`${trail.items.length} append-only audit kaydı yüklendi.`);
    });
  }

  function toggleMode(mode: string, checked: boolean) {
    setCompletedModes((current) =>
      checked ? [...current, mode] : current.filter((item) => item !== mode)
    );
    setApproveConfirmed(false);
  }

  async function approve() {
    if (
      !canApproveEditorialReview({
        detail,
        completedReviewModes: completedModes,
        confirmed: approveConfirmed,
        csrfToken
      }) ||
      !detail
    ) {
      setFeedback("Onay için tüm review modlarını tamamlayın, CSRF girin ve teyit verin.");
      return;
    }
    await execute(async () => {
      const result = await client().decideContentReview(
        detail.version.id,
        approvalRequest(completedModes)
      );
      setDetail(result);
      setQueue((current) =>
        current.filter((item) => item.version_id !== result.version.id)
      );
      setApproveConfirmed(false);
      setFeedback("CaseVersion APPROVED durumuna geçirildi; yayınlanmadı.");
    });
  }

  async function reject() {
    if (
      !canRejectEditorialReview({ detail, rationale: rejectRationale, csrfToken }) ||
      !detail
    ) {
      setFeedback("Ret için gerekçe ve aynı oturuma ait CSRF gereklidir.");
      return;
    }
    await execute(async () => {
      const result = await client().decideContentReview(
        detail.version.id,
        rejectionRequest(rejectRationale)
      );
      setDetail(result);
      setQueue((current) =>
        current.filter((item) => item.version_id !== result.version.id)
      );
      setCompletedModes([]);
      setRejectRationale("");
      setFeedback("CaseVersion gerekçeli olarak DRAFT'a döndürüldü; attestasyonlar temizlendi.");
    });
  }

  const approveEnabled = canApproveEditorialReview({
    detail,
    completedReviewModes: completedModes,
    confirmed: approveConfirmed,
    csrfToken
  });
  const rejectEnabled = canRejectEditorialReview({
    detail,
    rationale: rejectRationale,
    csrfToken
  });

  return (
    <main className={styles.shell}>
      <div className={styles.topbar}>
        <Link href="/">← Editorial Operations</Link>
        <Link href="/case-builder">Case Builder →</Link>
      </div>

      <header className={styles.hero}>
        <div>
          <p className="eyebrow">CAP-065 · Editorial Quality Gate</p>
          <h1>İçeriği değiştir­meden bağımsız kalite incelemesi</h1>
          <p>
            Bu çalışma alanı yalnız <strong>IN_REVIEW</strong> CaseVersion’ları okur.
            Onay, exact review-mode attestasyonu ve maker-checker ayrımıyla yapılır;
            ret gerekçeyle DRAFT’a döner. Yayınlama burada yoktur.
          </p>
        </div>
        <aside className={styles.boundary}>
          <strong>Yetki sınırı</strong>
          <span>
            Reviewer içeriği düzenleyemez, Flow’u değiştiremez ve publish/withdraw
            komutu veremez. Session ve CSRF tarayıcı depolamasına yazılmaz.
          </span>
        </aside>
      </header>

      <section className={styles.connection} aria-label="Admin bağlantısı">
        <label>
          Canonical API base URL
          <input
            value={apiBaseUrl}
            onChange={(event) => setApiBaseUrl(event.target.value)}
            placeholder="https://api.example.com"
            autoComplete="off"
          />
        </label>
        <label>
          Same-session CSRF
          <input
            type="password"
            value={csrfToken}
            onChange={(event) => setCsrfToken(event.target.value)}
            placeholder="Yalnız karar komutlarında kullanılır"
            autoComplete="off"
          />
        </label>
        <button type="button" disabled={busy} onClick={verifySession}>
          Oturumu doğrula
        </button>
        {session ? (
          <p className={styles.session}>
            Roller: {session.roles.join(", ") || "—"} · Yetkiler:{" "}
            {session.direct_capabilities.join(", ") || "rol üzerinden"}
          </p>
        ) : null}
      </section>

      <p className={styles.feedback} aria-live="polite">
        {feedback || "Hiçbir istek otomatik başlatılmaz."}
      </p>

      <section className={styles.filters} aria-label="İnceleme kuyruğu filtreleri">
        <label>
          Risk
          <input
            value={contentRisk}
            onChange={(event) => setContentRisk(event.target.value)}
            placeholder="L0 / L1 / L2"
          />
        </label>
        <label>
          Birincil alan
          <input
            value={primaryDomain}
            onChange={(event) => setPrimaryDomain(event.target.value)}
            placeholder="PUBLIC_LIFE"
          />
        </label>
        <label>
          Sayfa boyutu
          <input
            type="number"
            min={1}
            max={100}
            value={limit}
            onChange={(event) => setLimit(Number(event.target.value) || 25)}
          />
        </label>
        <label>
          Offset
          <input value={offset} readOnly aria-readonly="true" />
        </label>
        <button type="button" disabled={busy} onClick={() => loadQueue(0)}>
          Kuyruğu yükle
        </button>
      </section>

      <div className={styles.workspace}>
        <section className={styles.panel} aria-label="IN_REVIEW kuyruğu">
          <h2>İnceleme kuyruğu</h2>
          {queue.length === 0 ? (
            <p className={styles.empty}>
              Kuyruk yüklenmedi veya filtreyle eşleşen içerik bulunmadı.
            </p>
          ) : (
            <div className={styles.queue}>
              {queue.map((item) => (
                <button
                  type="button"
                  className={styles.queueItem}
                  aria-current={selectedVersionId === item.version_id}
                  key={item.version_id}
                  onClick={() => selectItem(item.version_id)}
                >
                  <strong>{item.title}</strong>
                  <span>
                    {item.content_risk} · {item.primary_domain_code} · v{item.version_no}
                  </span>
                  <small>{item.required_review_modes.join(", ") || "Review modu yok"}</small>
                </button>
              ))}
            </div>
          )}
          <div className={styles.pager}>
            <button
              type="button"
              disabled={busy || offset === 0}
              onClick={() => loadQueue(Math.max(0, offset - limit))}
            >
              Önceki
            </button>
            <button
              type="button"
              disabled={busy || nextOffset === null}
              onClick={() => nextOffset !== null && loadQueue(nextOffset)}
            >
              Sonraki
            </button>
          </div>
          <button
            type="button"
            disabled={busy || !selectedVersionId}
            onClick={loadDetail}
          >
            Seçili ayrıntıyı açıkça yükle
          </button>
        </section>

        <div className={styles.rightColumn}>
          <section className={styles.detail} aria-label="Salt okunur CaseVersion ayrıntısı">
            <h2>Salt okunur içerik</h2>
            {!detail ? (
              <p className={styles.empty}>
                Kuyruktan seçim yapmak istek başlatmaz. Ayrıntıyı ayrıca yükleyin.
              </p>
            ) : (
              <>
                <div className={styles.metaGrid}>
                  <div className={styles.metaCard}>
                    <strong>{detail.version.state}</strong>
                    <span>Lifecycle</span>
                  </div>
                  <div className={styles.metaCard}>
                    <strong>{detail.version.content_risk}</strong>
                    <span>Risk</span>
                  </div>
                  <div className={styles.metaCard}>
                    <strong>{detail.version.content_locale}</strong>
                    <span>Canonical locale</span>
                  </div>
                  <div className={styles.metaCard}>
                    <strong>v{detail.version.version_no}</strong>
                    <span>Immutable version identity</span>
                  </div>
                  <div className={styles.metaCard}>
                    <strong>{detail.version.flow_template_code}</strong>
                    <span>Read-only Flow identity</span>
                  </div>
                  <div className={styles.metaCard}>
                    <strong>{formattedDate(detail.submitted_at)}</strong>
                    <span>{detail.submitter_actor_ref}</span>
                  </div>
                </div>

                <div className={styles.readonlySection}>
                  <h3>{detail.version.title}</h3>
                  <p>{detail.version.summary}</p>
                  <p>
                    {detail.version.base_format_code} · {detail.version.primary_domain_code} ·{" "}
                    {detail.version.market_scope}
                  </p>
                </div>

                <div className={styles.readonlySection}>
                  <h3>Meseleler ve sorular</h3>
                  {detail.version.issues.map((issue) => (
                    <details key={issue.id}>
                      <summary>{issue.title}</summary>
                      <ul>
                        {issue.questions.map((question) => (
                          <li key={question.id}>
                            <strong>{question.stable_code}</strong> — {question.prompt}
                            <pre>{pretty(question.response_schema)}</pre>
                          </li>
                        ))}
                      </ul>
                    </details>
                  ))}
                </div>

                <div className={styles.readonlySection}>
                  <h3>Bağlam ve kaynaklar</h3>
                  <details>
                    <summary>{detail.version.context_blocks.length} bağlam bloğu</summary>
                    {detail.version.context_blocks.map((block) => (
                      <div key={block.id}>
                        <strong>{block.title}</strong>
                        <p>{block.body}</p>
                      </div>
                    ))}
                  </details>
                  <details>
                    <summary>{detail.version.sources.length} kaynak referansı</summary>
                    <ul>
                      {detail.version.sources.map((source) => (
                        <li key={source.id}>
                          <strong>{source.title}</strong> · {source.publisher || "Yayıncı yok"} ·{" "}
                          {source.verified ? "doğrulanmış" : "doğrulanmamış"}
                        </li>
                      ))}
                    </ul>
                  </details>
                  <details>
                    <summary>{detail.version.localizations.length} yerelleştirme</summary>
                    <ul>
                      {detail.version.localizations.map((item) => (
                        <li key={item.locale}>
                          <strong>{item.locale}</strong> — {item.title}
                        </li>
                      ))}
                    </ul>
                  </details>
                </div>
              </>
            )}
          </section>

          <section className={styles.decision} aria-label="İnceleme kararı">
            <h2>Bağımsız karar</h2>
            {!detail ? (
              <p className={styles.empty}>Karar için önce salt okunur ayrıntıyı yükleyin.</p>
            ) : detail.version.state !== "IN_REVIEW" ? (
              <p className={styles.empty}>
                Karar tamamlandı: {detail.version.state}. Publish burada sunulmaz.
              </p>
            ) : (
              <div className={styles.decisionGrid}>
                <div className={styles.actionBox}>
                  <h3>APPROVE</h3>
                  <p className={styles.empty}>
                    Her zorunlu review modunu bizzat tamamladığınızı attest edin.
                  </p>
                  <div className={styles.modeList}>
                    {detail.version.required_review_modes.length === 0 ? (
                      <span>Zorunlu review modu yok.</span>
                    ) : (
                      detail.version.required_review_modes.map((mode) => (
                        <label className={styles.checkRow} key={mode}>
                          <input
                            type="checkbox"
                            checked={completedModes.includes(mode)}
                            onChange={(event) => toggleMode(mode, event.target.checked)}
                          />
                          <span>{mode}</span>
                        </label>
                      ))
                    )}
                  </div>
                  <label className={styles.checkRow}>
                    <input
                      type="checkbox"
                      checked={approveConfirmed}
                      onChange={(event) => setApproveConfirmed(event.target.checked)}
                    />
                    <span>İçeriği değiştirmeden bağımsız değerlendirdiğimi onaylıyorum.</span>
                  </label>
                  <button type="button" disabled={busy || !approveEnabled} onClick={approve}>
                    Onayla · yayınlama yok
                  </button>
                </div>

                <div className={`${styles.actionBox} ${styles.reject}`}>
                  <h3>REJECT</h3>
                  <label>
                    Editöre dönüş gerekçesi
                    <textarea
                      value={rejectRationale}
                      maxLength={5000}
                      onChange={(event) => setRejectRationale(event.target.value)}
                      placeholder="Neyin yeniden düzenlenmesi gerektiğini açıkça yazın."
                    />
                  </label>
                  <button type="button" disabled={busy || !rejectEnabled} onClick={reject}>
                    Gerekçeyle DRAFT’a döndür
                  </button>
                </div>
              </div>
            )}
          </section>

          <section className={styles.audit} aria-label="Lifecycle audit">
            <div className="sectionHeading">
              <h2>Append-only audit</h2>
              <button type="button" disabled={busy || !detail} onClick={loadAudit}>
                Audit’i yükle
              </button>
            </div>
            {audit.length === 0 ? (
              <p className={styles.empty}>Audit otomatik yüklenmez.</p>
            ) : (
              <ul className={styles.auditList}>
                {audit.map((entry) => (
                  <li key={entry.audit_id}>
                    <strong>{entry.command}</strong> · {entry.previous_state ?? "∅"} →{" "}
                    {entry.new_state}
                    <small>
                      {entry.actor_ref} · {formattedDate(entry.occurred_at)}
                      {entry.rationale ? ` · ${entry.rationale}` : ""}
                    </small>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
