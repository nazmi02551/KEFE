"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import styles from "@/src/components/reason-moderation-workspace.module.css";
import type { AdminSession } from "@/src/lib/contracts";
import {
  ReasonModerationApiClient,
  ReasonModerationApiError
} from "@/src/lib/reason-moderation-api";
import {
  canSubmitModeration,
  moderationDecisionRequest,
  reportSummary,
  type ReasonModerationAuditEntry,
  type ReasonModerationDecision,
  type ReasonModerationItem,
  type ReasonModerationQueueKind,
  type ReasonReportCode
} from "@/src/lib/reason-moderation";

function messageFor(error: unknown): string {
  if (error instanceof ReasonModerationApiError) {
    return `${error.code}: ${error.message}`;
  }
  if (error instanceof Error) return error.message.slice(0, 500);
  return "Beklenmeyen bir hata oluştu.";
}

function formattedDate(value: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString("tr-TR");
}

export function ReasonModerationWorkspace({
  initialReasonId = ""
}: {
  initialReasonId?: string;
}) {
  const configuredBase = process.env.NEXT_PUBLIC_KEFE_API_BASE_URL ?? "";
  const [apiBaseUrl, setApiBaseUrl] = useState(configuredBase);
  const [csrfToken, setCsrfToken] = useState("");
  const [session, setSession] = useState<AdminSession | null>(null);
  const [kind, setKind] = useState<ReasonModerationQueueKind>("PENDING");
  const [caseVersionId, setCaseVersionId] = useState("");
  const [reportCode, setReportCode] = useState<ReasonReportCode | "">("");
  const [limit, setLimit] = useState(25);
  const [offset, setOffset] = useState(0);
  const [nextOffset, setNextOffset] = useState<number | null>(null);
  const [queue, setQueue] = useState<ReasonModerationItem[]>([]);
  const [selectedReasonId, setSelectedReasonId] = useState(initialReasonId);
  const [detail, setDetail] = useState<ReasonModerationItem | null>(null);
  const [audit, setAudit] = useState<ReasonModerationAuditEntry[]>([]);
  const [decision, setDecision] = useState<ReasonModerationDecision>("ALLOWED");
  const [rationale, setRationale] = useState("");
  const [confirmationReasonId, setConfirmationReasonId] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState("");

  const client = useMemo(
    () => () =>
      new ReasonModerationApiClient({
        baseUrl: apiBaseUrl,
        csrfToken
      }),
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

  function resetDecisionContext() {
    setDecision("ALLOWED");
    setRationale("");
    setConfirmationReasonId("");
    setConfirmed(false);
  }

  function resetInspection() {
    setDetail(null);
    setAudit([]);
    resetDecisionContext();
  }

  async function verifySession() {
    await execute(async () => {
      const resolved = await client().session();
      setSession(resolved);
      setFeedback("Moderator oturumu açık komutla doğrulandı.");
    });
  }

  async function loadQueue(targetOffset = 0) {
    await execute(async () => {
      const page = await client().queue({
        kind,
        limit,
        offset: targetOffset,
        case_version_id: caseVersionId.trim() || undefined,
        report_code: reportCode || undefined
      });
      setQueue(page.items);
      setOffset(targetOffset);
      setNextOffset(page.next_offset);
      setSelectedReasonId("");
      resetInspection();
      setFeedback(`${page.items.length} ${kind} Community Reason yüklendi.`);
    });
  }

  function selectReason(reasonId: string) {
    setSelectedReasonId(reasonId);
    resetInspection();
    setFeedback("Seçim yapıldı. Ayrıntı henüz yüklenmedi.");
  }

  async function loadDetail() {
    const reasonId = selectedReasonId.trim();
    if (!reasonId) {
      setFeedback("Exact Community Reason ID gereklidir.");
      return;
    }
    await execute(async () => {
      const loaded = await client().detail(reasonId);
      setDetail(loaded);
      setAudit([]);
      resetDecisionContext();
      setFeedback("Salt okunur neden ayrıntısı açık komutla yüklendi.");
    });
  }

  async function loadAudit() {
    if (!detail) {
      setFeedback("Önce neden ayrıntısını yükleyin.");
      return;
    }
    await execute(async () => {
      const trail = await client().audit(detail.reason_id);
      setAudit(trail.items);
      setFeedback(`${trail.items.length} append-only moderation kaydı yüklendi.`);
    });
  }

  async function submitDecision() {
    if (
      !canSubmitModeration({
        reason: detail,
        state: decision,
        rationale,
        confirmationReasonId,
        confirmed,
        csrfToken
      }) ||
      !detail
    ) {
      setFeedback(
        "Karar için 10–1000 karakter gerekçe, exact neden ID teyidi, onay kutusu ve aynı oturuma ait CSRF gereklidir."
      );
      return;
    }
    const reasonId = detail.reason_id;
    await execute(async () => {
      const result = await client().decide(
        reasonId,
        moderationDecisionRequest({
          reasonId,
          state: decision,
          rationale
        })
      );
      setDetail(result.reason);
      setAudit((current) => [result.audit, ...current]);
      setQueue((current) => current.filter((item) => item.reason_id !== reasonId));
      resetDecisionContext();
      setFeedback(
        `${result.audit.previous_state} → ${result.audit.decided_state} kararı atomik audit kaydıyla uygulandı.`
      );
    });
  }

  const canDecide = canSubmitModeration({
    reason: detail,
    state: decision,
    rationale,
    confirmationReasonId,
    confirmed,
    csrfToken
  });

  return (
    <main className={styles.shell}>
      <header className={styles.hero}>
        <div>
          <p className={styles.eyebrow}>CAP-066 · Admin Studio</p>
          <h1>Community Reason Moderation</h1>
          <p>
            PENDING ve yeni raporlanmış nedenleri privacy-safe aggregate bağlamla
            inceleyin. Hiçbir işlem otomatik başlamaz; her okuma ve karar ayrı bir
            komuttur.
          </p>
        </div>
        <Link className={styles.backLink} href="/">
          Admin Studio’ya dön
        </Link>
      </header>

      <section className={styles.securityPanel} aria-labelledby="security-title">
        <div>
          <p className={styles.eyebrow}>Oturum sınırı</p>
          <h2 id="security-title">API ve same-session CSRF</h2>
        </div>
        <label>
          Admin API base URL
          <input
            value={apiBaseUrl}
            onChange={(event) => setApiBaseUrl(event.target.value)}
            placeholder="https://admin-api.example"
            autoComplete="off"
          />
        </label>
        <label>
          CSRF token
          <input
            value={csrfToken}
            onChange={(event) => setCsrfToken(event.target.value)}
            type="password"
            autoComplete="off"
          />
        </label>
        <button type="button" onClick={verifySession} disabled={busy}>
          Oturumu doğrula
        </button>
        {session ? (
          <p className={styles.sessionSummary}>
            Roller: {session.roles.join(", ") || "—"} · Step-up: {formattedDate(session.step_up_at)}
          </p>
        ) : null}
      </section>

      <div className={styles.workspace}>
        <section className={styles.queuePanel} aria-labelledby="queue-title">
          <div className={styles.sectionHeading}>
            <div>
              <p className={styles.eyebrow}>Aday kuyruğu</p>
              <h2 id="queue-title">PENDING / REPORTED</h2>
            </div>
            <span>{queue.length} kayıt</span>
          </div>

          <div className={styles.filters}>
            <label>
              Kuyruk
              <select
                value={kind}
                onChange={(event) => {
                  setKind(event.target.value as ReasonModerationQueueKind);
                  setOffset(0);
                  setNextOffset(null);
                  setQueue([]);
                  setSelectedReasonId("");
                  resetInspection();
                }}
              >
                <option value="PENDING">PENDING</option>
                <option value="REPORTED">REPORTED</option>
              </select>
            </label>
            <label>
              Exact CaseVersion ID
              <input
                value={caseVersionId}
                onChange={(event) => setCaseVersionId(event.target.value)}
                autoComplete="off"
              />
            </label>
            <label>
              Report code
              <select
                value={reportCode}
                onChange={(event) =>
                  setReportCode(event.target.value as ReasonReportCode | "")
                }
              >
                <option value="">Tümü</option>
                <option value="ABUSE">ABUSE</option>
                <option value="PERSONAL_DATA">PERSONAL_DATA</option>
                <option value="MISLEADING">MISLEADING</option>
                <option value="OTHER">OTHER</option>
              </select>
            </label>
            <label>
              Sayfa boyutu
              <input
                type="number"
                min={1}
                max={100}
                value={limit}
                onChange={(event) =>
                  setLimit(Math.min(100, Math.max(1, Number(event.target.value) || 1)))
                }
              />
            </label>
          </div>

          <div className={styles.commandRow}>
            <button type="button" onClick={() => loadQueue(0)} disabled={busy}>
              Kuyruğu yükle
            </button>
            <button
              type="button"
              onClick={() => loadQueue(Math.max(0, offset - limit))}
              disabled={busy || offset === 0}
            >
              Önceki
            </button>
            <button
              type="button"
              onClick={() => nextOffset !== null && loadQueue(nextOffset)}
              disabled={busy || nextOffset === null}
            >
              Sonraki
            </button>
          </div>

          <div className={styles.queueList}>
            {queue.length === 0 ? (
              <p className={styles.empty}>Kuyruk açık komutla henüz yüklenmedi.</p>
            ) : (
              queue.map((item) => (
                <button
                  type="button"
                  className={
                    selectedReasonId === item.reason_id
                      ? styles.selectedQueueItem
                      : styles.queueItem
                  }
                  key={item.reason_id}
                  onClick={() => selectReason(item.reason_id)}
                >
                  <strong>{item.tags.join(" · ") || "Etiketsiz"}</strong>
                  <span>{item.moderation_state}</span>
                  <small>
                    {item.report_count} rapor · aday {formattedDate(item.candidate_at)}
                  </small>
                </button>
              ))
            )}
          </div>
        </section>

        <section className={styles.detailPanel} aria-labelledby="detail-title">
          <div className={styles.sectionHeading}>
            <div>
              <p className={styles.eyebrow}>Exact inspection</p>
              <h2 id="detail-title">Salt okunur neden</h2>
            </div>
          </div>

          <label>
            Community Reason ID
            <input
              value={selectedReasonId}
              onChange={(event) => {
                setSelectedReasonId(event.target.value);
                resetInspection();
              }}
              autoComplete="off"
            />
          </label>
          <div className={styles.commandRow}>
            <button type="button" onClick={loadDetail} disabled={busy}>
              Ayrıntıyı yükle
            </button>
            <button type="button" onClick={loadAudit} disabled={busy || !detail}>
              Audit’i yükle
            </button>
          </div>

          {detail ? (
            <div className={styles.detailCard}>
              <dl>
                <div>
                  <dt>Durum</dt>
                  <dd>{detail.moderation_state}</dd>
                </div>
                <div>
                  <dt>CaseVersion</dt>
                  <dd>{detail.case_version_id}</dd>
                </div>
                <div>
                  <dt>Etiketler</dt>
                  <dd>{detail.tags.join(", ") || "—"}</dd>
                </div>
                <div>
                  <dt>Oluşturulma</dt>
                  <dd>{formattedDate(detail.created_at)}</dd>
                </div>
              </dl>
              <article className={styles.reasonBody}>
                <h3>Neden metni</h3>
                <p>{detail.body ?? "Bu kayıt yalnız yapılandırılmış etiket içeriyor."}</p>
              </article>
              <div className={styles.reportBox}>
                <h3>Privacy-safe rapor özeti</h3>
                <p>Toplam: {detail.report_count}</p>
                <ul>
                  {reportSummary(detail).length ? (
                    reportSummary(detail).map((summary) => <li key={summary}>{summary}</li>)
                  ) : (
                    <li>Rapor yok</li>
                  )}
                </ul>
                <small>Son rapor: {formattedDate(detail.latest_reported_at)}</small>
              </div>
            </div>
          ) : (
            <p className={styles.empty}>Seçim ayrıntıyı otomatik yüklemez.</p>
          )}

          <div className={styles.decisionCard}>
            <h3>Explicit moderation kararı</h3>
            <label>
              Karar
              <select
                value={decision}
                onChange={(event) => {
                  setDecision(event.target.value as ReasonModerationDecision);
                  setConfirmed(false);
                }}
              >
                <option value="ALLOWED">ALLOWED</option>
                <option value="BLOCKED">BLOCKED</option>
              </select>
            </label>
            <label>
              İnsan gerekçesi (10–1000 karakter)
              <textarea
                value={rationale}
                onChange={(event) => {
                  setRationale(event.target.value);
                  setConfirmed(false);
                }}
                maxLength={1000}
                rows={5}
              />
            </label>
            <label>
              Exact neden ID teyidi
              <input
                value={confirmationReasonId}
                onChange={(event) => {
                  setConfirmationReasonId(event.target.value);
                  setConfirmed(false);
                }}
                autoComplete="off"
              />
            </label>
            <label className={styles.confirmation}>
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(event) => setConfirmed(event.target.checked)}
              />
              Bu kararın seçili immutable Community Reason kaydına uygulanacağını teyit ediyorum.
            </label>
            <button
              type="button"
              className={decision === "BLOCKED" ? styles.dangerButton : undefined}
              onClick={submitDecision}
              disabled={busy || !canDecide}
            >
              Kararı uygula
            </button>
          </div>

          <div className={styles.auditCard}>
            <h3>Append-only moderation audit</h3>
            {audit.length ? (
              <ol>
                {audit.map((entry) => (
                  <li key={entry.audit_id}>
                    <strong>
                      {entry.previous_state} → {entry.decided_state}
                    </strong>
                    <span>{entry.rationale}</span>
                    <small>
                      {entry.actor_ref} · {formattedDate(entry.created_at)}
                    </small>
                  </li>
                ))}
              </ol>
            ) : (
              <p className={styles.empty}>Audit açık komutla henüz yüklenmedi.</p>
            )}
          </div>
        </section>
      </div>

      <p className={styles.boundary}>
        Bu yüzey author veya reporter kimliği, kullanıcı skoru, otomatik karar, içerik
        düzenleme, toplu işlem, appeal ya da unblock sağlamaz.
      </p>
      <div className={styles.feedback} role="status" aria-live="polite">
        {busy ? "İşlem sürüyor…" : feedback}
      </div>
    </main>
  );
}
