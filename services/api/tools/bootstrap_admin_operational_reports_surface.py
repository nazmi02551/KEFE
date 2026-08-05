from __future__ import annotations

from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[3]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    content = target.read_text()
    if old not in content:
        raise RuntimeError(f"expected snippet not found in {path}: {old[:160]!r}")
    target.write_text(content.replace(old, new, 1))


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dedent(content).lstrip())


write(
    "apps/admin/app/operational-reports/page.tsx",
    """
    import { OperationalReportsWorkspace } from "@/src/components/operational-reports-workspace";

    export default function OperationalReportsPage() {
      return <OperationalReportsWorkspace />;
    }
    """,
)

write(
    "apps/admin/src/lib/operational-reports.ts",
    """
    export type OperationalSignal = "QUIET" | "NOMINAL" | "ATTENTION" | "CRITICAL";

    export interface OperationalThresholds {
      in_review_attention_threshold: number;
      pending_proposal_attention_threshold: number;
      moderation_candidate_attention_threshold: number;
    }

    export interface ContentSupplyPolicy {
      pending_dispatch_attention_threshold: number;
      queued_run_attention_threshold: number;
      unreviewed_proposal_attention_threshold: number;
      recent_non_success_attention_threshold: number;
      max_cycle_silence_seconds: number;
      failure_window_seconds: number;
    }

    export interface ContentSupplySnapshot {
      signal: OperationalSignal;
      as_of: string;
      reason_codes: string[];
      active_schedule_count: number;
      paused_schedule_count: number;
      due_schedule_count: number;
      pending_dispatch_count: number;
      running_dispatch_count: number;
      stale_dispatch_count: number;
      recent_dispatch_non_success_count: number;
      queued_ingestion_run_count: number;
      running_ingestion_run_count: number;
      stale_ingestion_lease_count: number;
      recent_failed_ingestion_run_count: number;
      unreviewed_proposal_count: number;
      running_cycle_count: number;
      stale_cycle_count: number;
      recent_non_success_cycle_count: number;
      latest_terminal_cycle_state: string | null;
      latest_terminal_cycle_completed_at: string | null;
      seconds_since_latest_terminal_cycle: number | null;
    }

    export interface OperationalReportsSnapshot {
      as_of: string;
      overall_signal: OperationalSignal;
      reason_codes: string[];
      thresholds: OperationalThresholds;
      content_supply_policy: ContentSupplyPolicy;
      content_supply: ContentSupplySnapshot;
      editorial_lifecycle: Record<string, number>;
      proposal_review: Record<string, number>;
      moderation: Record<string, number>;
      aggregate_only: true;
    }

    const SIGNAL_TEXT: Record<OperationalSignal, string> = {
      QUIET: "Sessiz",
      NOMINAL: "Normal",
      ATTENTION: "Dikkat",
      CRITICAL: "Kritik"
    };

    const REASON_TEXT: Record<string, string> = {
      CONTENT_SUPPLY_ATTENTION: "İçerik tedarik hattı dikkat gerektiriyor",
      CONTENT_SUPPLY_CRITICAL: "İçerik tedarik hattı kritik durumda",
      EDITORIAL_IN_REVIEW_BACKLOG: "İncelemedeki CaseVersion kuyruğu eşiği aştı",
      PROPOSAL_REVIEW_BACKLOG: "Bekleyen Proposal kuyruğu eşiği aştı",
      MODERATION_BACKLOG: "Aktif moderasyon kuyruğu eşiği aştı"
    };

    export function operationalSignalText(signal: OperationalSignal): string {
      return SIGNAL_TEXT[signal];
    }

    export function operationalReasonText(code: string): string {
      return REASON_TEXT[code] ?? code;
    }

    export function sortedCountEntries(
      values: Record<string, number>
    ): Array<[string, number]> {
      return Object.entries(values).sort(([left], [right]) => left.localeCompare(right));
    }

    export function totalOperationalCount(values: Record<string, number>): number {
      return Object.values(values).reduce((total, value) => total + value, 0);
    }

    export function boundedOperationalText(value: unknown, fallback: string): string {
      if (typeof value !== "string") return fallback;
      const trimmed = value.trim();
      return trimmed ? trimmed.slice(0, 1000) : fallback;
    }
    """,
)

write(
    "apps/admin/src/lib/operational-reports-api.ts",
    """
    import type { AdminSession } from "@/src/lib/contracts";
    import type { OperationalReportsSnapshot } from "@/src/lib/operational-reports";
    import { boundedOperationalText } from "@/src/lib/operational-reports";

    export class OperationalReportsApiError extends Error {
      readonly code: string;
      readonly status: number;

      constructor(code: string, message: string, status: number) {
        super(message);
        this.name = "OperationalReportsApiError";
        this.code = code;
        this.status = status;
      }
    }

    export interface OperationalReportsApiOptions {
      baseUrl: string;
      fetchImpl?: typeof fetch;
    }

    function normalizeBaseUrl(value: string): string {
      const trimmed = value.trim().replace(/\/+$/, "");
      if (!trimmed) {
        throw new OperationalReportsApiError(
          "ADMIN_API_BASE_REQUIRED",
          "Admin API base URL is required",
          0
        );
      }
      let parsed: URL;
      try {
        parsed = new URL(trimmed);
      } catch {
        throw new OperationalReportsApiError(
          "ADMIN_API_BASE_INVALID",
          "Admin API base URL is invalid",
          0
        );
      }
      const local = parsed.hostname === "localhost" || parsed.hostname === "127.0.0.1";
      if (parsed.protocol !== "https:" && !local) {
        throw new OperationalReportsApiError(
          "ADMIN_API_BASE_INSECURE",
          "Admin API requires HTTPS outside localhost",
          0
        );
      }
      return trimmed;
    }

    async function parseError(response: Response): Promise<OperationalReportsApiError> {
      const fallback = `Admin API request failed with HTTP ${response.status}`;
      let payload: unknown;
      try {
        payload = await response.json();
      } catch {
        return new OperationalReportsApiError(
          "ADMIN_API_HTTP_ERROR",
          fallback,
          response.status
        );
      }
      if (!payload || typeof payload !== "object") {
        return new OperationalReportsApiError(
          "ADMIN_API_HTTP_ERROR",
          fallback,
          response.status
        );
      }
      const record = payload as Record<string, unknown>;
      const nested =
        record.error && typeof record.error === "object"
          ? (record.error as Record<string, unknown>)
          : record;
      const code =
        typeof nested.code === "string" && nested.code.length <= 120
          ? nested.code
          : "ADMIN_API_HTTP_ERROR";
      return new OperationalReportsApiError(
        code,
        boundedOperationalText(nested.message ?? nested.detail, fallback),
        response.status
      );
    }

    export class OperationalReportsApiClient {
      private readonly baseUrl: string;
      private readonly fetchImpl: typeof fetch;

      constructor(options: OperationalReportsApiOptions) {
        this.baseUrl = normalizeBaseUrl(options.baseUrl);
        this.fetchImpl = options.fetchImpl ?? fetch;
      }

      private async get<T>(path: string): Promise<T> {
        const response = await this.fetchImpl(`${this.baseUrl}${path}`, {
          method: "GET",
          credentials: "include",
          headers: new Headers({ Accept: "application/json" }),
          cache: "no-store",
          redirect: "error"
        });
        if (!response.ok) throw await parseError(response);
        return (await response.json()) as T;
      }

      session(): Promise<AdminSession> {
        return this.get("/internal/admin/v1/session");
      }

      snapshot(): Promise<OperationalReportsSnapshot> {
        return this.get("/internal/admin/v1/operational-reports/snapshot");
      }
    }
    """,
)

write(
    "apps/admin/src/components/operational-reports-workspace.tsx",
    """
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
    """,
)

write(
    "apps/admin/src/components/operational-reports-workspace.module.css",
    """
    .shell {
      min-height: 100vh;
      padding: 32px;
      background: #f4f6f8;
      color: #17202a;
    }

    .hero,
    .connection,
    .signal,
    .supply,
    .thresholds,
    .empty,
    .boundary,
    .card {
      max-width: 1180px;
      margin: 0 auto 20px;
      border: 1px solid #d8dee5;
      border-radius: 18px;
      background: #ffffff;
      box-shadow: 0 10px 30px rgba(20, 30, 40, 0.06);
    }

    .hero,
    .signal,
    .supply {
      display: flex;
      justify-content: space-between;
      gap: 28px;
      padding: 28px;
    }

    .hero h1,
    .signal h2,
    .supply h2 {
      margin: 4px 0 10px;
    }

    .hero p,
    .connection p,
    .empty p,
    .thresholds p,
    .boundary p {
      max-width: 760px;
      line-height: 1.55;
    }

    .eyebrow {
      margin: 0;
      font-size: 0.76rem;
      font-weight: 800;
      letter-spacing: 0.12em;
      color: #526273;
    }

    .links {
      display: flex;
      flex-wrap: wrap;
      align-content: flex-start;
      gap: 10px;
    }

    .links a {
      padding: 9px 12px;
      border: 1px solid #c9d1da;
      border-radius: 999px;
      color: inherit;
      text-decoration: none;
    }

    .connection,
    .thresholds,
    .empty,
    .boundary {
      padding: 24px 28px;
    }

    .connection label {
      display: grid;
      gap: 8px;
      max-width: 620px;
      margin: 18px 0;
      font-weight: 700;
    }

    .connection input {
      padding: 12px 14px;
      border: 1px solid #bbc5cf;
      border-radius: 10px;
      font: inherit;
    }

    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }

    .actions button {
      padding: 11px 16px;
      border: 0;
      border-radius: 10px;
      background: #17202a;
      color: #ffffff;
      font: inherit;
      font-weight: 750;
      cursor: pointer;
    }

    .actions button:disabled {
      cursor: wait;
      opacity: 0.55;
    }

    .status {
      margin-bottom: 0;
      overflow-wrap: anywhere;
    }

    .error {
      color: #8d1b13;
      font-weight: 750;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 18px;
      max-width: 1180px;
      margin: 0 auto 20px;
    }

    .card {
      margin: 0;
      padding: 22px;
    }

    .cardHeading {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 18px;
    }

    .cardHeading h2 {
      font-size: 1.05rem;
    }

    .cardHeading strong {
      font-size: 2rem;
    }

    .card dl,
    .metrics,
    .thresholds dl {
      margin: 16px 0 0;
    }

    .metric {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      padding: 9px 0;
      border-top: 1px solid #e5e9ee;
    }

    .metric dt {
      overflow-wrap: anywhere;
    }

    .metric dd {
      margin: 0;
      font-weight: 800;
    }

    .metrics {
      min-width: 360px;
    }

    .signal ul {
      padding-left: 20px;
      line-height: 1.65;
    }

    .boundary {
      border-left: 6px solid #17202a;
    }

    @media (max-width: 860px) {
      .shell {
        padding: 16px;
      }

      .hero,
      .signal,
      .supply {
        display: block;
      }

      .links {
        margin-top: 20px;
      }

      .grid {
        grid-template-columns: 1fr;
      }

      .metrics {
        min-width: 0;
      }
    }
    """,
)

write(
    "apps/admin/tests/operational-reports.test.ts",
    """
    import assert from "node:assert/strict";
    import test from "node:test";

    import {
      operationalReasonText,
      operationalSignalText,
      sortedCountEntries,
      totalOperationalCount
    } from "../src/lib/operational-reports.ts";

    test("operational reports helpers keep signals and reasons explainable", () => {
      assert.equal(operationalSignalText("ATTENTION"), "Dikkat");
      assert.match(
        operationalReasonText("MODERATION_BACKLOG"),
        /moderasyon/i
      );
      assert.equal(operationalReasonText("UNKNOWN_CODE"), "UNKNOWN_CODE");
    });

    test("aggregate entries are deterministic and totalled without inference", () => {
      const values = { REPORTED: 2, PENDING: 3 };
      assert.deepEqual(sortedCountEntries(values), [
        ["PENDING", 3],
        ["REPORTED", 2]
      ]);
      assert.equal(totalOperationalCount(values), 5);
    });
    """,
)

write(
    "apps/admin/tests/operational-reports-api.test.ts",
    """
    import assert from "node:assert/strict";
    import test from "node:test";

    import {
      OperationalReportsApiClient,
      OperationalReportsApiError
    } from "../src/lib/operational-reports-api.ts";

    test("client construction and navigation cause no request", () => {
      let calls = 0;
      new OperationalReportsApiClient({
        baseUrl: "http://localhost:8000",
        fetchImpl: async () => {
          calls += 1;
          return new Response("{}", { status: 200 });
        }
      });
      assert.equal(calls, 0);
    });

    test("session and snapshot are explicit GET-only credentialed reads", async () => {
      const calls: Array<{ url: string; init?: RequestInit }> = [];
      const client = new OperationalReportsApiClient({
        baseUrl: "http://localhost:8000/",
        fetchImpl: async (input, init) => {
          calls.push({ url: String(input), init });
          return new Response(
            JSON.stringify(
              calls.length === 1
                ? {
                    admin_subject_id: "00000000-0000-0000-0000-000000000001",
                    session_id: "00000000-0000-0000-0000-000000000002",
                    roles: ["REVIEWER"],
                    direct_capabilities: [],
                    authenticated_at: "2026-08-05T00:00:00Z",
                    mfa_satisfied_at: null,
                    step_up_at: null,
                    expires_at: "2026-08-06T00:00:00Z"
                  }
                : {
                    as_of: "2026-08-05T00:00:00Z",
                    overall_signal: "NOMINAL",
                    reason_codes: [],
                    thresholds: {
                      in_review_attention_threshold: 50,
                      pending_proposal_attention_threshold: 100,
                      moderation_candidate_attention_threshold: 50
                    },
                    content_supply_policy: {},
                    content_supply: { signal: "NOMINAL", as_of: "2026-08-05T00:00:00Z", reason_codes: [] },
                    editorial_lifecycle: {},
                    proposal_review: {},
                    moderation: {},
                    aggregate_only: true
                  }
            ),
            { status: 200, headers: { "content-type": "application/json" } }
          );
        }
      });

      await client.session();
      await client.snapshot();
      assert.deepEqual(
        calls.map((call) => call.url),
        [
          "http://localhost:8000/internal/admin/v1/session",
          "http://localhost:8000/internal/admin/v1/operational-reports/snapshot"
        ]
      );
      for (const call of calls) {
        assert.equal(call.init?.method, "GET");
        assert.equal(call.init?.credentials, "include");
        assert.equal(call.init?.cache, "no-store");
        assert.equal(new Headers(call.init?.headers).has("X-KEFE-CSRF"), false);
        assert.equal(call.init?.body, undefined);
      }
    });

    test("remote HTTP base fails closed before a request", () => {
      assert.throws(
        () => new OperationalReportsApiClient({ baseUrl: "http://example.com" }),
        (error: unknown) =>
          error instanceof OperationalReportsApiError &&
          error.code === "ADMIN_API_BASE_INSECURE"
      );
    });
    """,
)

write(
    "apps/admin/tools/check_operational_reports_contract.mjs",
    """
    import fs from "node:fs";
    import path from "node:path";
    import process from "node:process";

    const root = process.cwd();
    const contract = JSON.parse(
      fs.readFileSync(
        path.resolve(root, "../../docs/contracts/admin-operational-reports-snapshot.v1.json"),
        "utf8"
      )
    );
    const component = fs.readFileSync(
      path.resolve(root, "src/components/operational-reports-workspace.tsx"),
      "utf8"
    );
    const helper = fs.readFileSync(path.resolve(root, "src/lib/operational-reports.ts"), "utf8");
    const api = fs.readFileSync(path.resolve(root, "src/lib/operational-reports-api.ts"), "utf8");
    const route = fs.readFileSync(path.resolve(root, "app/operational-reports/page.tsx"), "utf8");
    const home = fs.readFileSync(path.resolve(root, "app/page.tsx"), "utf8");
    const problems = [];

    if (contract.contract_id !== "admin-operational-reports-snapshot.v1") {
      problems.push("Operational Reports contract identity drifted");
    }
    if (contract.parent_runtime?.sha !== "6d5bc52388b590706a3a07aef9b2be08bc501aae") {
      problems.push("Operational Reports parent runtime drifted");
    }
    if (contract.capabilities?.primary?.join(",") !== "CAP-123") {
      problems.push("Operational Reports primary capability drifted");
    }
    if (contract.capabilities?.lifecycle_promotion !== false) {
      problems.push("Operational Reports cannot promote capability lifecycle");
    }
    if (contract.security?.new_capability !== "OPERATIONAL_REPORT_READ") {
      problems.push("Dedicated operational report capability is not locked");
    }
    if (contract.privacy?.aggregate_only !== true) {
      problems.push("Aggregate-only privacy boundary is not locked");
    }

    for (const fragment of [
      "OperationalReportsWorkspace",
      "verifySession",
      "loadSnapshot",
      "Admin Operational Reports",
      "Şeffaf reason codes",
      "Görünür eşikler",
      "Aggregate-only privacy boundary",
      "Snapshot yükle"
    ]) {
      if (!component.includes(fragment)) problems.push(`Workspace missing: ${fragment}`);
    }

    for (const forbidden of [
      "useEffect(",
      "setInterval(",
      "localStorage",
      "sessionStorage",
      "dangerouslySetInnerHTML",
      "X-KEFE-CSRF",
      "autoRefresh",
      "exportReport(",
      "acknowledgeReport(",
      "remediate("
    ]) {
      if (component.includes(forbidden)) {
        problems.push(`Workspace contains forbidden behavior: ${forbidden}`);
      }
    }

    for (const fragment of [
      "operationalSignalText",
      "operationalReasonText",
      "sortedCountEntries",
      "totalOperationalCount"
    ]) {
      if (!helper.includes(fragment)) problems.push(`Helper missing: ${fragment}`);
    }

    for (const fragment of [
      "OperationalReportsApiClient",
      "/internal/admin/v1/operational-reports/snapshot",
      "method: \"GET\"",
      "credentials: \"include\"",
      "cache: \"no-store\"",
      "ADMIN_API_BASE_INSECURE",
      "session()",
      "snapshot()"
    ]) {
      if (!api.includes(fragment)) problems.push(`API client missing: ${fragment}`);
    }
    for (const forbidden of ["X-KEFE-CSRF", "POST", "PUT", "PATCH", "DELETE", "localStorage", "setInterval("]) {
      if (api.includes(forbidden)) problems.push(`API client contains forbidden behavior: ${forbidden}`);
    }

    if (!route.includes("OperationalReportsWorkspace")) {
      problems.push("Operational Reports route is not wired");
    }
    if (!home.includes('href="/operational-reports"')) {
      problems.push("Admin Studio does not link Operational Reports");
    }

    if (problems.length) {
      console.error(problems.join("\n"));
      process.exit(1);
    }
    console.log(
      "Admin Operational Reports UI contract: PASS — explicit GET-only snapshot, " +
        "visible thresholds/reason codes, aggregate-only privacy and no polling, storage or mutation."
    );
    """,
)

replace_once(
    "apps/admin/app/page.tsx",
    """        <Link href="/reason-moderation">Community Reason Moderation alanını aç</Link>\n""",
    """        <Link href="/reason-moderation">Community Reason Moderation alanını aç</Link>\n        <Link href="/operational-reports">Operational Reports alanını aç</Link>\n""",
)
replace_once(
    "apps/admin/package.json",
    """node tools/check_reason_moderation_contract.mjs\"""",
    """node tools/check_reason_moderation_contract.mjs && node tools/check_operational_reports_contract.mjs\"""",
)

write(
    "apps/mobile/docs/admin-operational-reports-cross-surface-boundary.md",
    """
    # Admin Operational Reports cross-surface boundary

    The Admin Operational Reports snapshot is an internal, aggregate-only read model.

    - It does not add or alter any consumer/mobile endpoint.
    - It does not change CaseVersion publication, Flow pinning, decision sessions, reveal, My KEFE, Atlas or Community Reason visibility.
    - It reads existing content-supply, editorial lifecycle, Proposal review and moderation candidate authorities without storing a second report state.
    - No Case, Proposal, reason, actor, reporter, session, account, device, content, evidence, credential, secret or backend object-key data is returned.
    - No personality, ideology, psychometric, bias, causal or normative inference is produced.
    - Mobile and Global CI artifacts remain compile/upload evidence only. They are not a user release, production deployment or store submission.
    """,
)

write(
    "services/api/tools/check_admin_operational_reports_contract.py",
    """
    from __future__ import annotations

    import json
    from pathlib import Path

    ROOT = Path(__file__).resolve().parents[3]


    def text(path: str) -> str:
        return (ROOT / path).read_text(encoding="utf-8")


    def main() -> None:
        contract = json.loads(
            text("docs/contracts/admin-operational-reports-snapshot.v1.json")
        )
        problems: list[str] = []
        if contract["contract_id"] != "admin-operational-reports-snapshot.v1":
            problems.append("contract identity drifted")
        if contract["parent_runtime"]["sha"] != (
            "6d5bc52388b590706a3a07aef9b2be08bc501aae"
        ):
            problems.append("parent runtime drifted")
        if contract["capabilities"]["lifecycle_promotion"] is not False:
            problems.append("capability lifecycle promotion is forbidden")
        if contract["authority"]["second_analytics_store_allowed"] is not False:
            problems.append("second analytics authority is forbidden")
        if contract["privacy"]["aggregate_only"] is not True:
            problems.append("aggregate-only boundary is not locked")

        service = text(
            "services/api/src/kefe_api/modules/admin_operational_reports/service.py"
        )
        router = text(
            "services/api/src/kefe_api/modules/admin_security/operational_reports_router.py"
        )
        secured = text(
            "services/api/src/kefe_api/modules/admin_security/operational_reports.py"
        )
        models = text(
            "services/api/src/kefe_api/modules/admin_operational_reports/models.py"
        )
        main_source = text("services/api/src/kefe_api/main.py")
        policy = text(
            "services/api/src/kefe_api/modules/admin_security/policy.py"
        )
        authoring_port = text(
            "services/api/src/kefe_api/modules/content_authoring/ports.py"
        )
        proposal_port = text(
            "services/api/src/kefe_api/modules/ingestion_orchestration/ports.py"
        )
        reason_port = text(
            "services/api/src/kefe_api/modules/community_reason/ports.py"
        )
        memory_test = text(
            "services/api/tests/test_admin_operational_reports_http.py"
        )
        postgres_test = text(
            "services/api/tests/test_admin_operational_reports_http_postgres.py"
        )
        workflow = text(".github/workflows/admin-operational-reports.yml")
        cross_surface = text(
            "apps/mobile/docs/admin-operational-reports-cross-surface-boundary.md"
        )

        required = {
            "service": [
                "AdminOperationalReportsService",
                "content_supply.snapshot",
                "count_by_state",
                "count_proposal_queue",
                "count_moderation_queue",
                "MODERATION_BACKLOG",
                "PROPOSAL_REVIEW_BACKLOG",
                "EDITORIAL_IN_REVIEW_BACKLOG",
            ],
            "router": [
                'prefix="/internal/admin/v1/operational-reports"',
                '@router.get("/snapshot"',
                "aggregate_only",
                "content_supply_policy",
                "thresholds",
            ],
            "secured": [
                "OPERATIONAL_REPORT_READ",
                "self._security.authorize",
            ],
            "models": [
                "AdminOperationalSignal",
                "AdminOperationalReason",
                "reason_codes must be sorted and unique",
                "content supply snapshot must share report as_of",
            ],
            "main": [
                "AdminOperationalReportsService",
                "secured_admin_operational_reports_service",
                "admin_operational_reports_router",
            ],
            "policy": [
                "AdminCapability.OPERATIONAL_REPORT_READ",
                "AdminRole.REVIEWER",
                "AdminRole.PUBLISHER",
                "AdminRole.ACCESS_ADMIN",
            ],
            "authoring_port": ["count_by_state"],
            "proposal_port": ["count_proposal_queue"],
            "reason_port": ["count_moderation_queue"],
            "memory_test": [
                "requires_dedicated_capability",
                "authoritative_aggregate_counts",
                "privacy_safe",
                "threshold_driven",
                "status_code == 405",
            ],
            "postgres_test": [
                "survives_restart",
                "information_schema.tables",
                "reason_moderation_audit",
            ],
            "workflow": [
                "permissions:\n  contents: read",
                "api-memory",
                "admin-ui",
                "postgres",
                "Exact predecessor Community Reason moderation overlay",
                "Durable aggregate and restart proof",
            ],
            "cross_surface": [
                "does not add or alter any consumer/mobile endpoint",
                "compile/upload evidence only",
            ],
        }
        sources = {
            "service": service,
            "router": router,
            "secured": secured,
            "models": models,
            "main": main_source,
            "policy": policy,
            "authoring_port": authoring_port,
            "proposal_port": proposal_port,
            "reason_port": reason_port,
            "memory_test": memory_test,
            "postgres_test": postgres_test,
            "workflow": workflow,
            "cross_surface": cross_surface,
        }
        for name, fragments in required.items():
            for fragment in fragments:
                if fragment not in sources[name]:
                    problems.append(f"{name} missing {fragment}")

        for forbidden in (
            '@router.post("/snapshot"',
            '@router.put("/snapshot"',
            '@router.delete("/snapshot"',
            "localStorage",
            "sessionStorage",
            "setInterval(",
            "reporter_actor_id",
            "source_locator",
            "backend_object_key",
        ):
            if forbidden in router:
                problems.append(f"router contains forbidden fragment: {forbidden}")

        if (ROOT / ".github/workflows/_bootstrap-admin-operational-reports.yml").exists():
            problems.append("temporary bootstrap workflow remains")
        if (ROOT / "services/api/tools/bootstrap_admin_operational_reports_surface.py").exists():
            problems.append("temporary surface patcher remains")
        if (ROOT / "services/api/tools/bootstrap_admin_operational_reports.py").exists():
            problems.append("temporary backend patcher remains")

        if problems:
            raise SystemExit("\n".join(problems))
        print(
            "Admin Operational Reports backend contract: PASS — existing authorities, "
            "single-as-of aggregate snapshot, dedicated read capability, transparent "
            "thresholds and no persistence, identity payload or mutation path."
        )


    if __name__ == "__main__":
        main()
    """,
)

write(
    "services/api/tools/export_admin_operational_reports_openapi_overlay.py",
    """
    from __future__ import annotations

    import argparse
    import json
    import os
    from copy import deepcopy
    from pathlib import Path

    from export_openapi import _merge_overlay, build_openapi

    from kefe_api.core.settings import get_settings

    REPO_ROOT = Path(__file__).resolve().parents[3]
    CONTRACTS = REPO_ROOT / "docs" / "contracts"
    BASE = CONTRACTS / "openapi.v1.json"
    BEFORE_OPERATIONAL_REPORTS_OVERLAYS = (
        CONTRACTS / "openapi-consensus.v0.18.overlay.json",
        CONTRACTS / "openapi-mvp.v0.19.overlay.json",
        CONTRACTS / "openapi-admin-projection.v0.19.overlay.json",
        CONTRACTS / "openapi-admin-proposal-queue.v0.19.overlay.json",
        CONTRACTS / "openapi-admin-case-builder.v0.19.overlay.json",
        CONTRACTS / "openapi-admin-editorial-quality-review.v0.19.overlay.json",
        CONTRACTS / "openapi-admin-flow-composer.v0.19.overlay.json",
        CONTRACTS / "openapi-admin-publication-operations.v0.19.overlay.json",
        CONTRACTS / "openapi-admin-community-reason-moderation.v0.19.overlay.json",
    )
    EXPECTED_PATHS = ["/internal/admin/v1/operational-reports/snapshot"]


    def _load_before_contract() -> dict[str, object]:
        expected = deepcopy(json.loads(BASE.read_text(encoding="utf-8")))
        for overlay_path in BEFORE_OPERATIONAL_REPORTS_OVERLAYS:
            _merge_overlay(
                expected,
                json.loads(overlay_path.read_text(encoding="utf-8")),
                overlay_path.name,
            )
        return expected


    def _build_runtime_openapi() -> dict[str, object]:
        previous = os.environ.get("KEFE_API_VERSION")
        os.environ["KEFE_API_VERSION"] = "0.19.0"
        get_settings.cache_clear()
        try:
            return build_openapi()
        finally:
            if previous is None:
                os.environ.pop("KEFE_API_VERSION", None)
            else:
                os.environ["KEFE_API_VERSION"] = previous
            get_settings.cache_clear()


    def build_overlay() -> dict[str, object]:
        before = _load_before_contract()
        generated = _build_runtime_openapi()
        if generated.get("info", {}).get("version") != "0.19.0":
            raise SystemExit("Operational Reports overlay expects API version 0.19.0")

        before_schemas = before.get("components", {}).get("schemas", {})
        generated_schemas = generated.get("components", {}).get("schemas", {})
        before_paths = before.get("paths", {})
        generated_paths = generated.get("paths", {})
        changed_schemas = sorted(
            name
            for name in before_schemas.keys() & generated_schemas.keys()
            if before_schemas[name] != generated_schemas[name]
        )
        removed_schemas = sorted(before_schemas.keys() - generated_schemas.keys())
        changed_paths = sorted(
            path
            for path in before_paths.keys() & generated_paths.keys()
            if before_paths[path] != generated_paths[path]
        )
        removed_paths = sorted(before_paths.keys() - generated_paths.keys())
        if changed_schemas or removed_schemas or changed_paths or removed_paths:
            raise SystemExit(
                "Operational Reports API must remain additive; "
                f"changed_schemas={changed_schemas}, removed_schemas={removed_schemas}, "
                f"changed_paths={changed_paths}, removed_paths={removed_paths}"
            )

        missing = sorted(set(EXPECTED_PATHS) - set(generated_paths))
        already_present = sorted(set(EXPECTED_PATHS) & set(before_paths))
        if missing or already_present:
            raise SystemExit(
                "Operational Reports overlay path boundary drifted; "
                f"missing={missing}, already_present={already_present}"
            )
        new_path_names = sorted(EXPECTED_PATHS)
        referenced: set[str] = set()

        def collect(value: object) -> None:
            if isinstance(value, dict):
                ref = value.get("$ref")
                if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
                    referenced.add(ref.rsplit("/", 1)[-1])
                for item in value.values():
                    collect(item)
            elif isinstance(value, list):
                for item in value:
                    collect(item)

        for path in new_path_names:
            collect(generated_paths[path])
        processed: set[str] = set()
        while pending := sorted(referenced - processed):
            for name in pending:
                schema = generated_schemas.get(name)
                if schema is None:
                    raise SystemExit(
                        f"Operational Reports overlay references missing schema: {name}"
                    )
                processed.add(name)
                collect(schema)

        new_schema_names = set(generated_schemas) - set(before_schemas)
        unrelated = sorted(new_schema_names - referenced)
        if unrelated:
            raise SystemExit(
                f"Operational Reports overlay found unrelated schemas: {unrelated}"
            )
        additive = sorted(referenced & new_schema_names)
        return {
            "target_version": "0.19.0",
            "components": {
                "schemas": {name: generated_schemas[name] for name in additive}
            },
            "paths": {path: generated_paths[path] for path in new_path_names},
        }


    def main() -> None:
        parser = argparse.ArgumentParser(
            description="Generate additive Admin Operational Reports OpenAPI overlay"
        )
        parser.add_argument("--output", type=Path, required=True)
        parser.add_argument("--check", action="store_true")
        args = parser.parse_args()
        overlay = build_overlay()
        rendered = json.dumps(overlay, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.check:
            if not args.output.exists():
                raise SystemExit("Checked-in Operational Reports overlay is missing")
            if json.loads(args.output.read_text(encoding="utf-8")) != overlay:
                raise SystemExit("Checked-in Operational Reports overlay is stale")
            print(f"Operational Reports OpenAPI overlay matches {args.output}")
            return
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Operational Reports OpenAPI overlay written to {args.output}")


    if __name__ == "__main__":
        main()
    """,
)

replace_once(
    "services/api/tools/export_admin_community_reason_moderation_openapi_overlay.py",
    """    new_path_names = sorted(generated_paths.keys() - before_paths.keys())\n    if new_path_names != sorted(EXPECTED_PATHS):\n        raise SystemExit(f\"Reason moderation overlay path set drifted: {new_path_names}\")\n""",
    """    missing_paths = sorted(set(EXPECTED_PATHS) - set(generated_paths))\n    already_present = sorted(set(EXPECTED_PATHS) & set(before_paths))\n    if missing_paths or already_present:\n        raise SystemExit(\n            \"Reason moderation overlay path boundary drifted; \"\n            f\"missing={missing_paths}, already_present={already_present}\"\n        )\n    new_path_names = sorted(EXPECTED_PATHS)\n""",
)
replace_once(
    "services/api/tools/export_admin_community_reason_moderation_openapi_overlay.py",
    """    unrelated = sorted(new_schema_names - referenced_schema_names)\n    if unrelated:\n        raise SystemExit(f\"Reason moderation overlay found unrelated schemas: {unrelated}\")\n\n    additive_schema_names = sorted(referenced_schema_names & new_schema_names)\n""",
    """    additive_schema_names = sorted(referenced_schema_names & new_schema_names)\n""",
)

for path in (
    "services/api/tools/export_openapi.py",
    "services/api/tools/export_mvp_openapi_overlay.py",
    "services/api/tools/export_global_openapi_overlay.py",
):
    replace_once(
        path,
        """    \"openapi-admin-community-reason-moderation.v0.19.overlay.json\",\n"""
        if path.endswith("export_openapi.py")
        else """    CONTRACTS / \"openapi-admin-community-reason-moderation.v0.19.overlay.json\",\n""",
        (
            """    \"openapi-admin-community-reason-moderation.v0.19.overlay.json\",\n    \"openapi-admin-operational-reports.v0.19.overlay.json\",\n"""
            if path.endswith("export_openapi.py")
            else """    CONTRACTS / \"openapi-admin-community-reason-moderation.v0.19.overlay.json\",\n    CONTRACTS / \"openapi-admin-operational-reports.v0.19.overlay.json\",\n"""
        ),
    )

write(
    "services/api/tests/test_admin_operational_reports_http_postgres.py",
    """
    from __future__ import annotations

    import os
    from datetime import UTC, datetime, timedelta
    from uuid import UUID, uuid4

    import pytest
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine, text

    from kefe_api.core.settings import get_settings
    from kefe_api.main import create_app
    from kefe_api.modules.admin_security.router import ADMIN_SESSION_COOKIE
    from kefe_api.modules.ingestion_orchestration.models import (
        ExecutorKind,
        IngestionRun,
        IngestionRunState,
        InputArtifactKind,
        Proposal,
        ProposalReviewDecision,
        ProposalReviewDecisionKind,
        StageExecution,
        StageOutcome,
        stable_payload_hash,
    )

    pytestmark = pytest.mark.skipif(
        os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
        reason="PostgreSQL integration tests are opt-in",
    )

    ENDPOINT = "/internal/admin/v1/operational-reports/snapshot"


    def _seed_subject(database_url: str) -> UUID:
        subject_id = uuid4()
        now = datetime.now(UTC)
        engine = create_engine(database_url)
        with engine.begin() as connection:
            connection.execute(
                text("INSERT INTO admin_security.subject (id, state) VALUES (:id, 'ACTIVE')"),
                {"id": subject_id},
            )
            connection.execute(
                text(
                    """
                    INSERT INTO admin_security.role_assignment (
                        id, subject_id, role, granted_at
                    ) VALUES (:id, :subject_id, 'REVIEWER', :granted_at)
                    """
                ),
                {"id": uuid4(), "subject_id": subject_id, "granted_at": now},
            )
        return subject_id


    def _admin_client(app, subject_id: UUID) -> TestClient:
        now = datetime.now(UTC)
        issued = app.state.admin_session_store.issue(
            admin_subject_id=subject_id,
            authenticated_at=now,
            mfa_satisfied_at=now,
            expires_at=now + timedelta(hours=12),
        )
        client = TestClient(app)
        client.cookies.set(ADMIN_SESSION_COOKIE, issued.session_token)
        return client


    def _seed_editorial_states(database_url: str) -> None:
        engine = create_engine(database_url)
        now = datetime.now(UTC)
        states = ("DRAFT", "IN_REVIEW", "APPROVED", "PUBLISHED", "SUPERSEDED", "WITHDRAWN")
        with engine.begin() as connection:
            for state in states:
                case_id = uuid4()
                connection.execute(
                    text(
                        """
                        INSERT INTO editorial.case_item (id, slug, created_at)
                        VALUES (:id, :slug, :created_at)
                        """
                    ),
                    {"id": case_id, "slug": f"operational-{state.lower()}-{case_id.hex}", "created_at": now},
                )
                connection.execute(
                    text(
                        """
                        INSERT INTO editorial.case_version (
                            id, case_id, version_no, lifecycle_state, aggregate,
                            created_at, updated_at, published_at
                        ) VALUES (
                            :id, :case_id, 1, :state, '{}'::jsonb,
                            :created_at, :created_at, :published_at
                        )
                        """
                    ),
                    {
                        "id": uuid4(),
                        "case_id": case_id,
                        "state": state,
                        "created_at": now,
                        "published_at": now if state == "PUBLISHED" else None,
                    },
                )


    def _seed_proposal(app, decision: ProposalReviewDecisionKind | None) -> None:
        repository = app.state.ingestion_orchestration_repository
        now = datetime.now(UTC)
        run_id = uuid4()
        stage_id = uuid4()
        proposal_id = uuid4()
        repository.create_or_get_run(
            IngestionRun(
                id=run_id,
                run_key=f"operational-pg-{run_id}",
                input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
                input_artifact_id=uuid4(),
                input_content_hash="a" * 64,
                pipeline_code="OPERATIONAL_REPORT_PG",
                pipeline_version="1",
                configuration_hash="b" * 64,
                state=IngestionRunState.RUNNING,
                created_at=now,
                updated_at=now,
            )
        )
        repository.add_stage_execution(
            StageExecution(
                id=stage_id,
                run_id=run_id,
                stage_code="PROPOSE",
                stage_version="1",
                attempt_no=1,
                max_attempts=1,
                executor_kind=ExecutorKind.DETERMINISTIC,
                input_hash="c" * 64,
                started_at=now,
                outcome=StageOutcome.SUCCEEDED,
                output_hash="d" * 64,
                completed_at=now,
            )
        )
        payload = {"state": decision.value if decision else "PENDING"}
        repository.add_proposal(
            Proposal(
                id=proposal_id,
                proposal_kind="CASE_CANDIDATE",
                payload_schema_ref="urn:kefe:test:operational-report-pg",
                payload_schema_version="1",
                payload=payload,
                payload_hash=stable_payload_hash(payload),
                run_id=run_id,
                stage_execution_id=stage_id,
                created_at=now,
                risk_code="L0",
            )
        )
        if decision is not None:
            repository.add_review_decision(
                ProposalReviewDecision(
                    id=uuid4(),
                    proposal_id=proposal_id,
                    decision=decision,
                    reviewer_ref="test:pg-reviewer",
                    decided_at=now,
                )
            )


    def _seed_reason(database_url: str, state: str, *, reported: bool) -> None:
        engine = create_engine(database_url)
        now = datetime.now(UTC) - timedelta(minutes=5)
        author_id = uuid4()
        reporter_id = uuid4()
        case_id = uuid4()
        version_id = uuid4()
        session_id = uuid4()
        reason_id = uuid4()
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO identity.actor (id, actor_kind, state, created_at)
                    VALUES
                        (:author, 'GUEST', 'ACTIVE', :now),
                        (:reporter, 'GUEST', 'ACTIVE', :now)
                    """
                ),
                {"author": author_id, "reporter": reporter_id, "now": now},
            )
            connection.execute(
                text(
                    """
                    INSERT INTO content.case_item (
                        id, slug, base_format_code, primary_domain_code,
                        lifecycle_state, content_risk, created_at, updated_at
                    ) VALUES (
                        :id, :slug, 'DILEMMA', 'DAILY_LIFE',
                        'PUBLISHED', 'L0', :now, :now
                    )
                    """
                ),
                {"id": case_id, "slug": f"operational-reason-{case_id.hex}", "now": now},
            )
            connection.execute(
                text(
                    """
                    INSERT INTO content.case_version (
                        id, case_id, version_no, status, title, summary,
                        accepts_weighs, published_at, created_at,
                        base_format_code, primary_domain_code, content_risk
                    ) VALUES (
                        :id, :case_id, 1, 'PUBLISHED', 'Operational reason',
                        'Aggregate-only fixture', true, :now, :now,
                        'DILEMMA', 'DAILY_LIFE', 'L0'
                    )
                    """
                ),
                {"id": version_id, "case_id": case_id, "now": now},
            )
            connection.execute(
                text(
                    """
                    INSERT INTO decision.weigh_session (
                        id, actor_id, case_id, case_version_id, state,
                        commit_idempotency_key, started_at, committed_at,
                        created_at, updated_at
                    ) VALUES (
                        :id, :actor, :case_id, :version_id, 'COMMITTED',
                        :key, :now, :now, :now, :now
                    )
                    """
                ),
                {
                    "id": session_id,
                    "actor": author_id,
                    "case_id": case_id,
                    "version_id": version_id,
                    "key": f"operational-{session_id}",
                    "now": now,
                },
            )
            connection.execute(
                text(
                    """
                    INSERT INTO community.reason (
                        id, actor_id, session_id, case_version_id, tags, body,
                        moderation_state, created_at, updated_at
                    ) VALUES (
                        :id, :actor, :session, :version,
                        '["FAIRNESS"]'::jsonb, :body, :state, :now, :now
                    )
                    """
                ),
                {
                    "id": reason_id,
                    "actor": author_id,
                    "session": session_id,
                    "version": version_id,
                    "body": "Pending aggregate fixture" if state == "PENDING" else None,
                    "state": state,
                    "now": now,
                },
            )
            if reported:
                connection.execute(
                    text(
                        """
                        INSERT INTO community.reason_report (
                            id, reason_id, reporter_actor_id, report_code, created_at
                        ) VALUES (:id, :reason, :reporter, 'PERSONAL_DATA', :created_at)
                        """
                    ),
                    {
                        "id": uuid4(),
                        "reason": reason_id,
                        "reporter": reporter_id,
                        "created_at": now + timedelta(minutes=1),
                    },
                )


    def test_postgres_operational_report_aggregates_survive_restart(
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        database_url = os.environ["KEFE_DATABASE_URL"]
        monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
        get_settings.cache_clear()
        reviewer_subject = _seed_subject(database_url)
        _seed_editorial_states(database_url)

        try:
            first_app = create_app()
            _seed_proposal(first_app, None)
            _seed_proposal(first_app, ProposalReviewDecisionKind.ACCEPTED)
            _seed_proposal(first_app, ProposalReviewDecisionKind.REJECTED)
            _seed_proposal(first_app, ProposalReviewDecisionKind.CHANGES_REQUESTED)
            _seed_reason(database_url, "PENDING", reported=False)
            _seed_reason(database_url, "NOT_REQUIRED", reported=True)
            _seed_reason(database_url, "BLOCKED", reported=True)

            first = _admin_client(first_app, reviewer_subject).get(ENDPOINT)
            assert first.status_code == 200
            first_body = first.json()
            assert first_body["editorial_lifecycle"] == {
                "DRAFT": 1,
                "IN_REVIEW": 1,
                "APPROVED": 1,
                "PUBLISHED": 1,
                "SUPERSEDED": 1,
                "WITHDRAWN": 1,
            }
            assert first_body["proposal_review"] == {
                "PENDING": 1,
                "ACCEPTED": 1,
                "REJECTED": 1,
                "CHANGES_REQUESTED": 1,
            }
            assert first_body["moderation"] == {"PENDING": 1, "REPORTED": 1}
            assert first_body["as_of"] == first_body["content_supply"]["as_of"]

            second_app = create_app()
            second = _admin_client(second_app, reviewer_subject).get(ENDPOINT)
            assert second.status_code == 200
            second_body = second.json()
            for section in ("editorial_lifecycle", "proposal_review", "moderation"):
                assert second_body[section] == first_body[section]

            engine = create_engine(database_url)
            with engine.connect() as connection:
                report_tables = connection.execute(
                    text(
                        """
                        SELECT count(*)
                        FROM information_schema.tables
                        WHERE table_schema IN ('public', 'editorial', 'community')
                          AND table_name LIKE '%operational_report%'
                        """
                    )
                ).scalar_one()
                reason_moderation_audit = connection.execute(
                    text("SELECT count(*) FROM community.reason_moderation_audit")
                ).scalar_one()
            assert int(report_tables) == 0
            assert int(reason_moderation_audit) == 0
        finally:
            get_settings.cache_clear()
    """,
)

write(
    ".github/workflows/admin-operational-reports.yml",
    """
    name: Admin Operational Reports CI

    on:
      pull_request:
        paths:
          - "apps/admin/**"
          - "apps/mobile/docs/admin-operational-reports-cross-surface-boundary.md"
          - "services/api/src/kefe_api/modules/admin_operational_reports/**"
          - "services/api/src/kefe_api/modules/admin_security/operational_reports.py"
          - "services/api/src/kefe_api/modules/admin_security/operational_reports_router.py"
          - "services/api/src/kefe_api/modules/admin_security/models.py"
          - "services/api/src/kefe_api/modules/admin_security/policy.py"
          - "services/api/src/kefe_api/modules/content_authoring/**"
          - "services/api/src/kefe_api/modules/ingestion_orchestration/**"
          - "services/api/src/kefe_api/modules/community_reason/**"
          - "services/api/src/kefe_api/infrastructure/postgres_flow_pinned_content_authoring.py"
          - "services/api/src/kefe_api/infrastructure/postgres_proposal_review_queue.py"
          - "services/api/src/kefe_api/infrastructure/postgres_community_reason.py"
          - "services/api/src/kefe_api/main.py"
          - "services/api/tests/test_admin_operational_reports_http.py"
          - "services/api/tests/test_admin_operational_reports_http_postgres.py"
          - "services/api/tools/check_admin_operational_reports_contract.py"
          - "services/api/tools/export_admin_operational_reports_openapi_overlay.py"
          - "services/api/tools/export_admin_community_reason_moderation_openapi_overlay.py"
          - "services/api/tools/export_openapi.py"
          - "services/api/tools/export_mvp_openapi_overlay.py"
          - "services/api/tools/export_global_openapi_overlay.py"
          - "docs/adr/0106-admin-operational-reports-snapshot.md"
          - "docs/contracts/admin-operational-reports-snapshot.v1.json"
          - "docs/contracts/openapi-admin-operational-reports.v0.19.overlay.json"
          - ".github/workflows/admin-operational-reports.yml"
      push:
        branches: [main]
        paths:
          - "apps/admin/**"
          - "apps/mobile/docs/admin-operational-reports-cross-surface-boundary.md"
          - "services/api/src/kefe_api/modules/admin_operational_reports/**"
          - "services/api/src/kefe_api/modules/admin_security/operational_reports.py"
          - "services/api/src/kefe_api/modules/admin_security/operational_reports_router.py"
          - "services/api/src/kefe_api/modules/admin_security/models.py"
          - "services/api/src/kefe_api/modules/admin_security/policy.py"
          - "services/api/src/kefe_api/modules/content_authoring/**"
          - "services/api/src/kefe_api/modules/ingestion_orchestration/**"
          - "services/api/src/kefe_api/modules/community_reason/**"
          - "services/api/src/kefe_api/infrastructure/postgres_flow_pinned_content_authoring.py"
          - "services/api/src/kefe_api/infrastructure/postgres_proposal_review_queue.py"
          - "services/api/src/kefe_api/infrastructure/postgres_community_reason.py"
          - "services/api/src/kefe_api/main.py"
          - "services/api/tests/test_admin_operational_reports_http.py"
          - "services/api/tests/test_admin_operational_reports_http_postgres.py"
          - "services/api/tools/check_admin_operational_reports_contract.py"
          - "services/api/tools/export_admin_operational_reports_openapi_overlay.py"
          - "services/api/tools/export_admin_community_reason_moderation_openapi_overlay.py"
          - "services/api/tools/export_openapi.py"
          - "services/api/tools/export_mvp_openapi_overlay.py"
          - "services/api/tools/export_global_openapi_overlay.py"
          - "docs/adr/0106-admin-operational-reports-snapshot.md"
          - "docs/contracts/admin-operational-reports-snapshot.v1.json"
          - "docs/contracts/openapi-admin-operational-reports.v0.19.overlay.json"
          - ".github/workflows/admin-operational-reports.yml"

    permissions:
      contents: read

    concurrency:
      group: admin-operational-reports-${{ github.workflow }}-${{ github.ref }}
      cancel-in-progress: true

    jobs:
      api-memory:
        runs-on: ubuntu-24.04
        timeout-minutes: 20
        steps:
          - uses: actions/checkout@v4
            with:
              show-progress: false
          - uses: actions/setup-python@v5
            with:
              python-version: "3.12"
              cache: pip
              cache-dependency-path: services/api/pyproject.toml
          - name: Install API
            working-directory: services/api
            run: python -m pip install -q -U pip && pip install -q -e '.[dev]'
          - name: Lint Operational Reports slice
            working-directory: services/api
            run: >-
              ruff check
              src/kefe_api/modules/admin_operational_reports
              src/kefe_api/modules/admin_security/operational_reports.py
              src/kefe_api/modules/admin_security/operational_reports_router.py
              src/kefe_api/modules/content_authoring/ports.py
              src/kefe_api/modules/content_authoring/in_memory.py
              src/kefe_api/modules/ingestion_orchestration/review_queue.py
              src/kefe_api/modules/ingestion_orchestration/ports.py
              src/kefe_api/modules/ingestion_orchestration/in_memory.py
              src/kefe_api/modules/community_reason/ports.py
              src/kefe_api/modules/community_reason/in_memory.py
              src/kefe_api/infrastructure/postgres_flow_pinned_content_authoring.py
              src/kefe_api/infrastructure/postgres_proposal_review_queue.py
              src/kefe_api/infrastructure/postgres_community_reason.py
              src/kefe_api/modules/admin_security/models.py
              src/kefe_api/modules/admin_security/policy.py
              src/kefe_api/main.py
              tests/test_admin_operational_reports_http.py
              tests/test_admin_operational_reports_http_postgres.py
              tools/check_admin_operational_reports_contract.py
              tools/export_admin_operational_reports_openapi_overlay.py
              tools/export_admin_community_reason_moderation_openapi_overlay.py
              tools/export_openapi.py
              tools/export_mvp_openapi_overlay.py
              tools/export_global_openapi_overlay.py
          - name: Executable backend architecture contract
            working-directory: services/api
            run: python tools/check_admin_operational_reports_contract.py
          - name: Exact Operational Reports OpenAPI overlay
            working-directory: services/api
            run: >-
              python tools/export_admin_operational_reports_openapi_overlay.py
              --output ../../docs/contracts/openapi-admin-operational-reports.v0.19.overlay.json
              --check
          - name: Exact predecessor Community Reason moderation overlay
            working-directory: services/api
            run: >-
              python tools/export_admin_community_reason_moderation_openapi_overlay.py
              --output ../../docs/contracts/openapi-admin-community-reason-moderation.v0.19.overlay.json
              --check
          - name: Full composed OpenAPI drift gate
            working-directory: services/api
            run: python tools/export_openapi.py --check ../../docs/contracts/openapi.v1.json
          - name: Memory authorization, privacy and aggregate behavior
            working-directory: services/api
            run: >-
              pytest -q
              tests/test_admin_operational_reports_http.py
              tests/test_admin_community_reason_moderation_http.py
              tests/test_mvp_completion.py

      admin-ui:
        runs-on: ubuntu-24.04
        timeout-minutes: 20
        defaults:
          run:
            working-directory: apps/admin
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-node@v4
            with:
              node-version: "22.13.0"
              cache: npm
              cache-dependency-path: apps/admin/package-lock.json
          - name: Install locked Admin dependencies
            run: npm ci --no-audit --no-fund
          - name: Verify Admin contracts, lint, types, tests and production build
            env:
              NEXT_TELEMETRY_DISABLED: "1"
            run: npm run verify

      postgres:
        needs: api-memory
        runs-on: ubuntu-24.04
        timeout-minutes: 20
        services:
          postgres:
            image: postgres:17-alpine
            env:
              POSTGRES_DB: kefe
              POSTGRES_USER: kefe
              POSTGRES_PASSWORD: kefe
            ports:
              - 5432:5432
            options: >-
              --health-cmd "pg_isready -U kefe -d kefe"
              --health-interval 5s
              --health-timeout 3s
              --health-retries 20
        steps:
          - uses: actions/checkout@v4
            with:
              show-progress: false
          - uses: actions/setup-python@v5
            with:
              python-version: "3.12"
              cache: pip
              cache-dependency-path: services/api/pyproject.toml
          - name: Install API
            working-directory: services/api
            run: python -m pip install -q -U pip && pip install -q -e '.[dev]'
          - name: Migrate PostgreSQL
            working-directory: services/api
            env:
              KEFE_DATABASE_URL: postgresql+psycopg://kefe:kefe@localhost:5432/kefe
            run: alembic upgrade head
          - name: Durable aggregate and restart proof
            working-directory: services/api
            env:
              KEFE_DATABASE_URL: postgresql+psycopg://kefe:kefe@localhost:5432/kefe
              KEFE_PERSISTENCE_BACKEND: postgres
              KEFE_RUN_POSTGRES_TESTS: "1"
            run: pytest -q tests/test_admin_operational_reports_http_postgres.py
    """,
)

print("Admin operational reports surface bootstrap applied")
