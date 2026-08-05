"use client";

import Link from "next/link";
import { useState } from "react";

import styles from "@/src/components/operational-reports-workspace.module.css";
import { OperationalReportsApiClient } from "@/src/lib/operational-reports-api";
import type { AdminSession } from "@/src/lib/contracts";
import type { OperationalReportsSnapshot } from "@/src/lib/operational-reports";
import {
  operationalReasonText,
  operationalSignalText,
  sortedCountEntries,
  totalOperationalCount
} from "@/src/lib/operational-reports";

const DEFAULT_BASE_URL = "http://localhost:8000";

export function OperationalReportsWorkspace() {
  const [baseUrl, setBaseUrl] = useState(DEFAULT_BASE_URL);
  const [session, setSession] = useState<AdminSession | null>(null);
  const [snapshot, setSnapshot] = useState<OperationalReportsSnapshot | null>(null);
  const [busy, setBusy] = useState<"session" | "snapshot" | null>(null);
  const [error, setError] = useState("");

  function client(): OperationalReportsApiClient {
    return new OperationalReportsApiClient({ baseUrl });
  }

  async function verifySession() {
    setBusy("session");
    setError("");
    try {
      setSession(await client().session());
    } catch (cause) {
      setSession(null);
      setError(cause instanceof Error ? cause.message : "Oturum doğrulanamadı");
    } finally {
      setBusy(null);
    }
  }

  async function loadSnapshot() {
    setBusy("snapshot");
    setError("");
    try {
      setSnapshot(await client().snapshot());
    } catch (cause) {
      setSnapshot(null);
      setError(cause instanceof Error ? cause.message : "Snapshot yüklenemedi");
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className={styles.shell}>
      <header className={styles.hero}>
        <div>
          <p className={styles.eyebrow}>CAP-123 · READ-ONLY</p>
          <h1>Admin Operational Reports</h1>
          <p>
            Mevcut otoritelerden üretilen, aggregate-only operasyonel snapshot.
            Bu yüzey analytics deposu, izleme sistemi veya üretim SLO kanıtı değildir.
          </p>
        </div>
        <nav aria-label="İlgili Admin çalışma alanları" className={styles.links}>
          <Link href="/case-builder">Case Builder</Link>
          <Link href="/publication-operations">Publication Operations</Link>
          <Link href="/reason-moderation">Reason Moderation</Link>
        </nav>
      </header>

      <section className={styles.connection} aria-labelledby="connection-heading">
        <div>
          <h2 id="connection-heading">Açık komutlar</h2>
          <p>Route yüklenmesi, odak veya navigation ağ isteği başlatmaz.</p>
        </div>
        <label>
          Admin API base URL
          <input
            value={baseUrl}
            onChange={(event) => setBaseUrl(event.target.value)}
            inputMode="url"
            autoComplete="off"
          />
        </label>
        <div className={styles.actions}>
          <button type="button" onClick={verifySession} disabled={busy !== null}>
            {busy === "session" ? "Doğrulanıyor…" : "Oturumu doğrula"}
          </button>
          <button type="button" onClick={loadSnapshot} disabled={busy !== null}>
            {busy === "snapshot" ? "Yükleniyor…" : "Snapshot yükle"}
          </button>
        </div>
        {session ? (
          <p className={styles.status}>
            Oturum: {session.admin_subject_id} · Roller: {session.roles.join(", ")}
          </p>
        ) : null}
        {error ? <p role="alert" className={styles.error}>{error}</p> : null}
      </section>

      {!snapshot ? (
        <section className={styles.empty}>
          <h2>Henüz snapshot yüklenmedi</h2>
          <p>Veri yalnız “Snapshot yükle” komutuyla okunur; polling ve auto-refresh yoktur.</p>
        </section>
      ) : (
        <>
          <section className={styles.signal} aria-labelledby="signal-heading">
            <div>
              <p className={styles.eyebrow}>OVERALL SIGNAL</p>
              <h2 id="signal-heading">
                {operationalSignalText(snapshot.overall_signal)}
              </h2>
              <p>As of: {new Date(snapshot.as_of).toLocaleString("tr-TR")}</p>
            </div>
            <div>
              <h3>Şeffaf reason codes</h3>
              {snapshot.reason_codes.length === 0 ? (
                <p>Aktif reason code yok.</p>
              ) : (
                <ul>
                  {snapshot.reason_codes.map((code) => (
                    <li key={code}>{operationalReasonText(code)} · {code}</li>
                  ))}
                </ul>
              )}
            </div>
          </section>

          <section className={styles.grid} aria-label="Aggregate operasyonel sayımlar">
            <CountCard title="Editorial lifecycle" values={snapshot.editorial_lifecycle} />
            <CountCard title="Proposal review" values={snapshot.proposal_review} />
            <CountCard title="Moderation candidates" values={snapshot.moderation} />
          </section>

          <section className={styles.supply} aria-labelledby="supply-heading">
            <div>
              <p className={styles.eyebrow}>EXISTING AUTHORITY</p>
              <h2 id="supply-heading">Content Supply Health</h2>
              <p>
                {operationalSignalText(snapshot.content_supply.signal)} · {snapshot.content_supply.reason_codes.join(", ") || "reason code yok"}
              </p>
            </div>
            <dl className={styles.metrics}>
              <Metric label="Aktif schedule" value={snapshot.content_supply.active_schedule_count} />
              <Metric label="Due schedule" value={snapshot.content_supply.due_schedule_count} />
              <Metric label="Pending dispatch" value={snapshot.content_supply.pending_dispatch_count} />
              <Metric label="Queued ingestion" value={snapshot.content_supply.queued_ingestion_run_count} />
              <Metric label="Unreviewed Proposal" value={snapshot.content_supply.unreviewed_proposal_count} />
              <Metric label="Stale cycle" value={snapshot.content_supply.stale_cycle_count} />
            </dl>
          </section>

          <section className={styles.thresholds} aria-labelledby="threshold-heading">
            <h2 id="threshold-heading">Görünür eşikler</h2>
            <dl>
              <Metric label="IN_REVIEW dikkat eşiği" value={snapshot.thresholds.in_review_attention_threshold} />
              <Metric label="PENDING Proposal dikkat eşiği" value={snapshot.thresholds.pending_proposal_attention_threshold} />
              <Metric label="Moderasyon aday dikkat eşiği" value={snapshot.thresholds.moderation_candidate_attention_threshold} />
            </dl>
            <p>
              Eşikler server policy’sinden gelir; tarayıcı bunları göndermez veya değiştirmez.
            </p>
          </section>

          <aside className={styles.boundary}>
            <strong>Aggregate-only privacy boundary</strong>
            <p>
              Case, Proposal, reason, actor, author, reporter, session, hesap, cihaz,
              içerik, rationale, raw evidence, source locator, credential, secret veya
              backend object key bu payload’da bulunmaz.
            </p>
          </aside>
        </>
      )}
    </main>
  );
}

function CountCard({ title, values }: { title: string; values: Record<string, number> }) {
  return (
    <article className={styles.card}>
      <div className={styles.cardHeading}>
        <h2>{title}</h2>
        <strong>{totalOperationalCount(values)}</strong>
      </div>
      <dl>
        {sortedCountEntries(values).map(([key, value]) => (
          <Metric key={key} label={key} value={value} />
        ))}
      </dl>
    </article>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className={styles.metric}>
      <dt>{label}</dt>
      <dd>{value.toLocaleString("tr-TR")}</dd>
    </div>
  );
}
