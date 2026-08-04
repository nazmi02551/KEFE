"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import styles from "@/src/components/publication-operations-workspace.module.css";
import { AdminApiClient, AdminApiError } from "@/src/lib/admin-api";
import type { AdminSession, AuthoringAuditEntry } from "@/src/lib/contracts";
import {
  canPublish,
  canWithdraw,
  preflightFingerprint,
  publishRequest,
  withdrawRequest,
  type PublicationDetail,
  type PublicationPreflight,
  type PublicationQueueItem,
  type PublicationQueueState
} from "@/src/lib/publication-operations";

function messageFor(error: unknown): string {
  if (error instanceof AdminApiError) return `${error.code}: ${error.message}`;
  if (error instanceof Error) return error.message.slice(0, 500);
  return "Beklenmeyen bir hata oluştu.";
}

function formattedDate(value: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString("tr-TR");
}

function pretty(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

export function PublicationOperationsWorkspace({
  initialVersionId = ""
}: {
  initialVersionId?: string;
}) {
  const configuredBase = process.env.NEXT_PUBLIC_KEFE_API_BASE_URL ?? "";
  const [apiBaseUrl, setApiBaseUrl] = useState(configuredBase);
  const [csrfToken, setCsrfToken] = useState("");
  const [session, setSession] = useState<AdminSession | null>(null);
  const [queueState, setQueueState] = useState<PublicationQueueState>("APPROVED");
  const [contentRisk, setContentRisk] = useState("");
  const [primaryDomain, setPrimaryDomain] = useState("");
  const [limit, setLimit] = useState(25);
  const [offset, setOffset] = useState(0);
  const [nextOffset, setNextOffset] = useState<number | null>(null);
  const [queue, setQueue] = useState<PublicationQueueItem[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState(initialVersionId);
  const [detail, setDetail] = useState<PublicationDetail | null>(null);
  const [preflight, setPreflight] = useState<PublicationPreflight | null>(null);
  const [preflightKey, setPreflightKey] = useState("");
  const [audit, setAudit] = useState<AuthoringAuditEntry[]>([]);
  const [publishConfirmed, setPublishConfirmed] = useState(false);
  const [withdrawRationale, setWithdrawRationale] = useState("");
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

  function resetInspection() {
    setDetail(null);
    setPreflight(null);
    setPreflightKey("");
    setAudit([]);
    setPublishConfirmed(false);
    setWithdrawRationale("");
  }

  async function verifySession() {
    await execute(async () => {
      const resolved = await client().session();
      setSession(resolved);
      setFeedback("Publisher oturumu açık komutla doğrulandı.");
    });
  }

  async function loadQueue(targetOffset = 0) {
    await execute(async () => {
      const page = await client().publicationOperations({
        state: queueState,
        limit,
        offset: targetOffset,
        content_risk: contentRisk.trim() || undefined,
        primary_domain_code: primaryDomain.trim() || undefined
      });
      setQueue(page.items);
      setOffset(targetOffset);
      setNextOffset(page.next_offset);
      setSelectedVersionId("");
      resetInspection();
      setFeedback(`${page.items.length} ${queueState} CaseVersion yüklendi.`);
    });
  }

  function selectItem(versionId: string) {
    setSelectedVersionId(versionId);
    resetInspection();
    setFeedback("Seçim yapıldı. Ayrıntı henüz yüklenmedi.");
  }

  async function loadDetail() {
    const normalized = selectedVersionId.trim();
    if (!normalized) {
      setFeedback("Exact CaseVersion ID gereklidir.");
      return;
    }
    await execute(async () => {
      const loaded = await client().publicationOperation(normalized);
      setDetail(loaded);
      setPreflight(null);
      setPreflightKey("");
      setAudit([]);
      setPublishConfirmed(false);
      setWithdrawRationale("");
      setFeedback("Salt okunur yayın ayrıntısı açık komutla yüklendi.");
    });
  }

  async function runPreflight() {
    if (!detail || detail.version.state !== "APPROVED") {
      setFeedback("Preflight için APPROVED CaseVersion ayrıntısı yüklenmelidir.");
      return;
    }
    await execute(async () => {
      const result = await client().publicationPreflight(detail.version.id);
      setPreflight(result);
      setPreflightKey(preflightFingerprint(result));
      setPublishConfirmed(false);
      setFeedback(
        result.eligible
          ? "Advisory preflight uygun. Yayın komutu yine güncel kuralları yeniden çalıştıracak."
          : `${result.validation_failures.length} yayın engeli bulundu.`
      );
    });
  }

  async function loadAudit() {
    if (!detail) {
      setFeedback("Önce yayın ayrıntısını yükleyin.");
      return;
    }
    await execute(async () => {
      const trail = await client().caseAudit(detail.version.case_id);
      setAudit(trail.items);
      setFeedback(`${trail.items.length} append-only lifecycle kaydı yüklendi.`);
    });
  }

  async function publish() {
    if (
      !canPublish({
        detail,
        preflight,
        confirmed: publishConfirmed,
        csrfToken
      }) ||
      !detail ||
      !preflight
    ) {
      setFeedback(
        "Yayın için uygun advisory preflight, aynı oturuma ait CSRF ve immutable sürüm teyidi gereklidir."
      );
      return;
    }
    const expectedKey = preflightFingerprint(preflight);
    if (expectedKey !== preflightKey) {
      setPublishConfirmed(false);
      setFeedback("Preflight görünümü değişti. Yeniden çalıştırın ve tekrar teyit verin.");
      return;
    }
    await execute(async () => {
      const result = await client().decidePublication(
        detail.version.id,
        publishRequest()
      );
      const loaded = await client().publicationOperation(result.version.id);
      setDetail(loaded);
      setQueue((current) =>
        current.filter((item) => item.version_id !== result.version.id)
      );
      setPreflight(null);
      setPreflightKey("");
      setPublishConfirmed(false);
      setFeedback(
        "CaseVersion PUBLISHED durumuna geçirildi ve exact Content Configuration/Flow provenance pinlendi."
      );
    });
  }

  async function withdraw() {
    if (!canWithdraw({ detail, rationale: withdrawRationale, csrfToken }) || !detail) {
      setFeedback("Geri çekme için gerekçe ve aynı oturuma ait CSRF gereklidir.");
      return;
    }
    await execute(async () => {
      const result = await client().decidePublication(
        detail.version.id,
        withdrawRequest(withdrawRationale)
      );
      const loaded = await client().publicationOperation(result.version.id);
      setDetail(loaded);
      setQueue((current) =>
        current.filter((item) => item.version_id !== result.version.id)
      );
      setWithdrawRationale("");
      setFeedback(
        "CaseVersion WITHDRAWN durumuna geçirildi; immutable yayın sürümü ve provenance silinmedi."
      );
    });
  }

  return (
    <main className={styles.shell}>
      <header className={styles.hero}>
        <div>
          <p className={styles.eyebrow}>KEFE · Admin Studio · CAP-065</p>
          <h1>Publication Operations</h1>
          <p>
            Onaylı içerikleri yayın öncesi inceler, advisory preflight çalıştırır ve
            ayrı publisher aktörüyle açık publish veya rationale-bound withdraw
            komutu verir.
          </p>
        </div>
        <Link className={styles.backLink} href="/">
          Editoryal operasyonlara dön
        </Link>
      </header>

      <section className={styles.boundary} aria-label="Yetki ve kapsam sınırı">
        <strong>İstekler otomatik başlamaz.</strong> Preflight rezervasyon değildir;
        publish güncel doğrulama ve Flow çözümlemesini tekrar çalıştırır. Bu yüzey
        içerik düzenlemez, onaylamaz veya Content Configuration yayımlamaz.
      </section>

      <section className={styles.connection}>
        <div>
          <label htmlFor="publication-api-base">Admin API</label>
          <input
            id="publication-api-base"
            value={apiBaseUrl}
            onChange={(event) => setApiBaseUrl(event.target.value)}
            placeholder="https://api.example.test"
          />
        </div>
        <div>
          <label htmlFor="publication-csrf">Aynı oturum CSRF</label>
          <input
            id="publication-csrf"
            type="password"
            autoComplete="off"
            value={csrfToken}
            onChange={(event) => setCsrfToken(event.target.value)}
          />
        </div>
        <button disabled={busy} onClick={verifySession} type="button">
          Oturumu doğrula
        </button>
        {session ? (
          <p className={styles.sessionSummary}>
            Roller: {session.roles.join(", ") || "—"} · Step-up: {formattedDate(session.step_up_at)}
          </p>
        ) : null}
      </section>

      <section className={styles.queueControls}>
        <div>
          <label htmlFor="publication-state">Kuyruk</label>
          <select
            id="publication-state"
            value={queueState}
            onChange={(event) => {
              setQueueState(event.target.value as PublicationQueueState);
              setQueue([]);
              setOffset(0);
              setNextOffset(null);
              setSelectedVersionId("");
              resetInspection();
            }}
          >
            <option value="APPROVED">APPROVED · yayın adayları</option>
            <option value="PUBLISHED">PUBLISHED · geri çekme adayları</option>
          </select>
        </div>
        <div>
          <label htmlFor="publication-risk">Risk · exact</label>
          <input
            id="publication-risk"
            value={contentRisk}
            onChange={(event) => setContentRisk(event.target.value)}
            placeholder="L0"
          />
        </div>
        <div>
          <label htmlFor="publication-domain">Domain · exact</label>
          <input
            id="publication-domain"
            value={primaryDomain}
            onChange={(event) => setPrimaryDomain(event.target.value)}
            placeholder="DAILY_LIFE"
          />
        </div>
        <div>
          <label htmlFor="publication-limit">Sayfa boyutu</label>
          <input
            id="publication-limit"
            type="number"
            min={1}
            max={100}
            value={limit}
            onChange={(event) => setLimit(Number(event.target.value))}
          />
        </div>
        <button disabled={busy} onClick={() => loadQueue(0)} type="button">
          Kuyruğu yükle
        </button>
      </section>

      <section className={styles.workspace}>
        <aside className={styles.queuePanel}>
          <div className={styles.panelHeader}>
            <h2>{queueState} kuyruğu</h2>
            <span>Offset {offset}</span>
          </div>
          <div className={styles.queueList}>
            {queue.map((item) => (
              <button
                className={
                  item.version_id === selectedVersionId
                    ? styles.queueItemSelected
                    : styles.queueItem
                }
                key={item.version_id}
                onClick={() => selectItem(item.version_id)}
                type="button"
              >
                <strong>{item.title}</strong>
                <span>{item.content_risk} · {item.primary_domain_code}</span>
                <small>v{item.version_no} · {item.flow_template_code} v{item.flow_template_version_no}</small>
              </button>
            ))}
            {queue.length === 0 ? <p className={styles.empty}>Kuyruk yüklenmedi veya boş.</p> : null}
          </div>
          <div className={styles.pagination}>
            <button
              disabled={busy || offset === 0}
              onClick={() => loadQueue(Math.max(0, offset - limit))}
              type="button"
            >
              Önceki
            </button>
            <button
              disabled={busy || nextOffset === null}
              onClick={() => nextOffset !== null && loadQueue(nextOffset)}
              type="button"
            >
              Sonraki
            </button>
          </div>
        </aside>

        <section className={styles.detailPanel}>
          <div className={styles.exactLoader}>
            <label htmlFor="publication-version-id">Exact CaseVersion ID</label>
            <div>
              <input
                id="publication-version-id"
                value={selectedVersionId}
                onChange={(event) => {
                  setSelectedVersionId(event.target.value);
                  resetInspection();
                }}
              />
              <button disabled={busy} onClick={loadDetail} type="button">
                Ayrıntıyı yükle
              </button>
            </div>
          </div>

          {detail ? (
            <>
              <div className={styles.detailHeader}>
                <div>
                  <p className={styles.eyebrow}>{detail.version.state}</p>
                  <h2>{detail.version.title}</h2>
                  <p>{detail.version.summary}</p>
                </div>
                <dl>
                  <div><dt>Risk</dt><dd>{detail.version.content_risk}</dd></div>
                  <div><dt>Domain</dt><dd>{detail.version.primary_domain_code}</dd></div>
                  <div><dt>Locale</dt><dd>{detail.version.content_locale}</dd></div>
                  <div><dt>Yayımlandı</dt><dd>{formattedDate(detail.version.published_at)}</dd></div>
                </dl>
              </div>

              <div className={styles.auditContext}>
                <article>
                  <h3>Son onay</h3>
                  <p>{detail.approval?.actor_ref ?? "Canonical approve audit bulunamadı"}</p>
                  <small>{formattedDate(detail.approval?.occurred_at ?? null)}</small>
                </article>
                <article>
                  <h3>Yayın provenance</h3>
                  <pre>{pretty(detail.pin)}</pre>
                </article>
              </div>

              <details className={styles.rawDetail}>
                <summary>Salt okunur CaseVersion içeriğini göster</summary>
                <pre>{pretty(detail.version)}</pre>
              </details>

              {detail.version.state === "APPROVED" ? (
                <section className={styles.actionCard}>
                  <div className={styles.actionHeader}>
                    <div>
                      <p className={styles.eyebrow}>APPROVED → PUBLISHED</p>
                      <h3>Yayın öncesi kontrol</h3>
                    </div>
                    <button disabled={busy} onClick={runPreflight} type="button">
                      Advisory preflight çalıştır
                    </button>
                  </div>
                  {preflight ? (
                    <div className={preflight.eligible ? styles.preflightOk : styles.preflightBlocked}>
                      <strong>{preflight.eligible ? "Uygun" : "Engelli"}</strong>
                      <p>Bu sonuç yalnız anlık kontroldür; state veya provenance rezerve etmez.</p>
                      <pre>{pretty(preflight)}</pre>
                    </div>
                  ) : null}
                  <label className={styles.confirmation}>
                    <input
                      checked={publishConfirmed}
                      disabled={!preflight?.eligible}
                      onChange={(event) => setPublishConfirmed(event.target.checked)}
                      type="checkbox"
                    />
                    Bu CaseVersion’ın yayımlandığında immutable olacağını ve komutun
                    doğrulamayı yeniden çalıştıracağını kabul ediyorum.
                  </label>
                  <button
                    className={styles.publishButton}
                    disabled={busy || !canPublish({ detail, preflight, confirmed: publishConfirmed, csrfToken })}
                    onClick={publish}
                    type="button"
                  >
                    Yayımla · güncel doğrulamayı tekrar çalıştır
                  </button>
                </section>
              ) : null}

              {detail.version.state === "PUBLISHED" ? (
                <section className={styles.actionCard}>
                  <p className={styles.eyebrow}>PUBLISHED → WITHDRAWN</p>
                  <h3>Yayından geri çek</h3>
                  <label htmlFor="withdraw-rationale">Zorunlu gerekçe</label>
                  <textarea
                    id="withdraw-rationale"
                    maxLength={5000}
                    rows={5}
                    value={withdrawRationale}
                    onChange={(event) => setWithdrawRationale(event.target.value)}
                  />
                  <button
                    className={styles.withdrawButton}
                    disabled={busy || !canWithdraw({ detail, rationale: withdrawRationale, csrfToken })}
                    onClick={withdraw}
                    type="button"
                  >
                    Gerekçeyle yayından çek
                  </button>
                </section>
              ) : null}

              <section className={styles.auditSection}>
                <div className={styles.actionHeader}>
                  <h3>Append-only lifecycle audit</h3>
                  <button disabled={busy} onClick={loadAudit} type="button">
                    Audit yükle
                  </button>
                </div>
                {audit.map((item) => (
                  <article key={item.audit_id}>
                    <strong>{item.command}</strong>
                    <span>{item.actor_ref}</span>
                    <span>{item.previous_state ?? "∅"} → {item.new_state}</span>
                    <small>{formattedDate(item.occurred_at)}</small>
                    {item.rationale ? <p>{item.rationale}</p> : null}
                  </article>
                ))}
              </section>
            </>
          ) : (
            <div className={styles.emptyDetail}>
              <h2>Yayın ayrıntısı yüklenmedi</h2>
              <p>Kuyruktan seçim yapmak istek başlatmaz. Exact ayrıntıyı ayrıca yükleyin.</p>
            </div>
          )}
        </section>
      </section>

      <p className={styles.feedback} role="status" aria-live="polite">
        {busy ? "İşlem sürüyor…" : feedback}
      </p>
    </main>
  );
}
