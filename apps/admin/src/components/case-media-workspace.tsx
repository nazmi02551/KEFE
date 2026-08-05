"use client";

import Link from "next/link";
import { useState } from "react";

import styles from "@/src/components/case-media-workspace.module.css";
import { CaseMediaApiClient } from "@/src/lib/case-media-api";
import type {
  MediaAsset,
  MediaAuditEntry,
  MediaKind,
  MediaSlot,
  MediaState,
  RegisterMediaRequest
} from "@/src/lib/case-media";
import type { AdminSession } from "@/src/lib/contracts";

const DEFAULT_BASE_URL = "http://localhost:8000";
const EMPTY_REGISTRATION: RegisterMediaRequest = {
  asset_key: "",
  kind: "IMAGE",
  delivery_ref: "",
  content_hash: "",
  byte_length: 1,
  media_type: "image/webp",
  title: "",
  alt_text: "",
  caption: null,
  credit_label: "",
  source_label: "",
  poster_asset_key: null
};

export function CaseMediaWorkspace() {
  const [baseUrl, setBaseUrl] = useState(DEFAULT_BASE_URL);
  const [csrfToken, setCsrfToken] = useState("");
  const [session, setSession] = useState<AdminSession | null>(null);
  const [stateFilter, setStateFilter] = useState<MediaState | "">("");
  const [assets, setAssets] = useState<MediaAsset[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [selected, setSelected] = useState<MediaAsset | null>(null);
  const [audit, setAudit] = useState<MediaAuditEntry[]>([]);
  const [registration, setRegistration] = useState(EMPTY_REGISTRATION);
  const [caseVersionId, setCaseVersionId] = useState("");
  const [slot, setSlot] = useState<MediaSlot>("HERO");
  const [priority, setPriority] = useState(100);
  const [muted, setMuted] = useState(false);
  const [looping, setLooping] = useState(false);
  const [busy, setBusy] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  function client(write = false): CaseMediaApiClient {
    return new CaseMediaApiClient({
      baseUrl,
      csrfToken: write ? csrfToken : undefined
    });
  }

  async function command(name: string, action: () => Promise<void>) {
    setBusy(name);
    setError("");
    setNotice("");
    try {
      await action();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Admin media command failed");
    } finally {
      setBusy("");
    }
  }

  function updateRegistration<Key extends keyof RegisterMediaRequest>(
    key: Key,
    value: RegisterMediaRequest[Key]
  ) {
    setRegistration((current) => ({ ...current, [key]: value }));
  }

  async function verifySession() {
    await command("session", async () => setSession(await client().session()));
  }

  async function loadInventory() {
    await command("inventory", async () => {
      const response = await client().inventory(stateFilter || undefined);
      setAssets(response.items);
      setNotice(`${response.items.length} media record loaded.`);
    });
  }

  async function loadDetail() {
    await command("detail", async () => {
      setSelected(await client().detail(selectedId));
      setAudit([]);
    });
  }

  async function loadAudit() {
    await command("audit", async () => {
      setAudit((await client().audit(selectedId)).items);
    });
  }

  async function register() {
    await command("register", async () => {
      const response = await client(true).register(registration);
      setSelectedId(response.asset.media_asset_id);
      setSelected(response.asset);
      setNotice(response.replayed ? "Exact registration replayed." : "Media metadata registered.");
    });
  }

  async function markReady() {
    await command("ready", async () => {
      const response = await client(true).markReady(selectedId);
      setSelected(response.asset);
      setNotice(response.replayed ? "Asset was already READY." : "Asset marked READY.");
    });
  }

  async function bind() {
    await command("bind", async () => {
      const response = await client(true).bind(selectedId, {
        case_version_id: caseVersionId,
        slot,
        priority,
        autoplay: false,
        muted,
        looping
      });
      setNotice(response.replayed ? "Exact binding replayed." : "Asset bound to CaseVersion.");
    });
  }

  async function retire() {
    await command("retire", async () => {
      const response = await client(true).retire(selectedId);
      setSelected(response.asset);
      setNotice(response.replayed ? "Asset was already RETIRED." : "Asset retired.");
    });
  }

  return (
    <main className={styles.shell}>
      <header className={styles.hero}>
        <div>
          <p className={styles.eyebrow}>CAP-094 · PROVIDER-NEUTRAL</p>
          <h1>Case Media Registry</h1>
          <p>
            Immutable metadata and explicit CaseVersion bindings. This workspace does not
            upload files, generate signed URLs or certify CDN availability.
          </p>
        </div>
        <nav aria-label="Related Admin workspaces" className={styles.links}>
          <Link href="/case-builder">Case Builder</Link>
          <Link href="/publication-operations">Publication Operations</Link>
          <Link href="/operational-reports">Operational Reports</Link>
        </nav>
      </header>

      <section className={styles.panel} aria-labelledby="connection-heading">
        <h2 id="connection-heading">Explicit connection commands</h2>
        <p>Route load, focus, selection and field changes never trigger requests.</p>
        <div className={styles.formGrid}>
          <label>
            Admin API base URL
            <input value={baseUrl} onChange={(event) => setBaseUrl(event.target.value)} />
          </label>
          <label>
            Same-session CSRF token
            <input
              type="password"
              value={csrfToken}
              onChange={(event) => setCsrfToken(event.target.value)}
              autoComplete="off"
            />
          </label>
          <label>
            Inventory state filter
            <select
              value={stateFilter}
              onChange={(event) => setStateFilter(event.target.value as MediaState | "")}
            >
              <option value="">All states</option>
              <option value="REGISTERED">REGISTERED</option>
              <option value="READY">READY</option>
              <option value="RETIRED">RETIRED</option>
            </select>
          </label>
        </div>
        <div className={styles.actions}>
          <button type="button" onClick={verifySession} disabled={Boolean(busy)}>
            Verify session
          </button>
          <button type="button" onClick={loadInventory} disabled={Boolean(busy)}>
            Load inventory
          </button>
        </div>
        {session ? (
          <p className={styles.status}>
            Session: {session.admin_subject_id} · {session.roles.join(", ")}
          </p>
        ) : null}
        {notice ? <p className={styles.status}>{notice}</p> : null}
        {error ? <p role="alert" className={styles.error}>{error}</p> : null}
      </section>

      <section className={styles.columns}>
        <article className={styles.panel}>
          <h2>Register immutable metadata</h2>
          <p>No binary body, file input, provider credential or public URL is accepted.</p>
          <div className={styles.formGrid}>
            <TextField label="Asset key" value={registration.asset_key} onChange={(value) => updateRegistration("asset_key", value)} />
            <label>
              Kind
              <select
                value={registration.kind}
                onChange={(event) => {
                  const kind = event.target.value as MediaKind;
                  updateRegistration("kind", kind);
                  updateRegistration("media_type", kind === "IMAGE" ? "image/webp" : "video/mp4");
                }}
              >
                <option value="IMAGE">IMAGE</option>
                <option value="VIDEO">VIDEO</option>
              </select>
            </label>
            <TextField label="Opaque delivery ref" value={registration.delivery_ref} onChange={(value) => updateRegistration("delivery_ref", value)} />
            <TextField label="SHA-256" value={registration.content_hash} onChange={(value) => updateRegistration("content_hash", value)} />
            <label>
              Byte length
              <input
                type="number"
                min={1}
                max={1_073_741_824}
                value={registration.byte_length}
                onChange={(event) => updateRegistration("byte_length", Number(event.target.value))}
              />
            </label>
            <TextField label="Media type" value={registration.media_type} onChange={(value) => updateRegistration("media_type", value)} />
            <TextField label="Title" value={registration.title} onChange={(value) => updateRegistration("title", value)} />
            <TextField label="Alt text" value={registration.alt_text} onChange={(value) => updateRegistration("alt_text", value)} />
            <TextField label="Caption (optional)" value={registration.caption ?? ""} onChange={(value) => updateRegistration("caption", value || null)} />
            <TextField label="Credit label" value={registration.credit_label} onChange={(value) => updateRegistration("credit_label", value)} />
            <TextField label="Source label" value={registration.source_label} onChange={(value) => updateRegistration("source_label", value)} />
            <TextField label="Poster asset key (optional)" value={registration.poster_asset_key ?? ""} onChange={(value) => updateRegistration("poster_asset_key", value || null)} />
          </div>
          <div className={styles.actions}>
            <button type="button" onClick={register} disabled={Boolean(busy)}>
              Register metadata
            </button>
          </div>
        </article>

        <article className={styles.panel}>
          <h2>Inspect and manage one asset</h2>
          <label>
            Exact media asset ID
            <input value={selectedId} onChange={(event) => setSelectedId(event.target.value)} />
          </label>
          <div className={styles.actions}>
            <button type="button" onClick={loadDetail} disabled={Boolean(busy) || !selectedId}>
              Load detail
            </button>
            <button type="button" onClick={loadAudit} disabled={Boolean(busy) || !selectedId}>
              Load audit
            </button>
            <button type="button" onClick={markReady} disabled={Boolean(busy) || !selectedId}>
              Mark READY
            </button>
            <button type="button" onClick={retire} disabled={Boolean(busy) || !selectedId}>
              Retire
            </button>
          </div>
          {selected ? <AssetDetails asset={selected} /> : <p>No detail loaded.</p>}
        </article>
      </section>

      <section className={styles.columns}>
        <article className={styles.panel}>
          <h2>Bind READY asset to exact CaseVersion</h2>
          <div className={styles.formGrid}>
            <TextField label="CaseVersion ID" value={caseVersionId} onChange={setCaseVersionId} />
            <label>
              Presentation slot
              <select value={slot} onChange={(event) => setSlot(event.target.value as MediaSlot)}>
                <option value="HERO">HERO</option>
                <option value="CONTEXT">CONTEXT</option>
                <option value="REVEAL">REVEAL</option>
                <option value="IMPACT">IMPACT</option>
              </select>
            </label>
            <label>
              Priority
              <input
                type="number"
                min={1}
                max={1_000_000}
                value={priority}
                onChange={(event) => setPriority(Number(event.target.value))}
              />
            </label>
            <label className={styles.checkLabel}>
              <input type="checkbox" checked={muted} onChange={(event) => setMuted(event.target.checked)} />
              Muted (video only)
            </label>
            <label className={styles.checkLabel}>
              <input type="checkbox" checked={looping} onChange={(event) => setLooping(event.target.checked)} />
              Looping (video only)
            </label>
          </div>
          <p>Autoplay is always false and cannot be enabled in this workspace.</p>
          <div className={styles.actions}>
            <button
              type="button"
              onClick={bind}
              disabled={Boolean(busy) || !selectedId || !caseVersionId}
            >
              Bind asset
            </button>
          </div>
        </article>

        <article className={styles.panel}>
          <h2>Append-only audit</h2>
          {audit.length === 0 ? (
            <p>No audit loaded.</p>
          ) : (
            <ol className={styles.auditList}>
              {audit.map((entry) => (
                <li key={entry.audit_id}>
                  <strong>{entry.command}</strong> · {entry.previous_state ?? "NONE"} → {entry.new_state}
                  <span>{new Date(entry.occurred_at).toLocaleString("tr-TR")}</span>
                </li>
              ))}
            </ol>
          )}
        </article>
      </section>

      <section className={styles.panel}>
        <h2>Loaded inventory</h2>
        {assets.length === 0 ? (
          <p>No inventory loaded.</p>
        ) : (
          <div className={styles.tableWrap}>
            <table>
              <thead>
                <tr>
                  <th>Asset key</th>
                  <th>Kind</th>
                  <th>State</th>
                  <th>Media type</th>
                  <th>Registered</th>
                </tr>
              </thead>
              <tbody>
                {assets.map((asset) => (
                  <tr key={asset.media_asset_id}>
                    <td>{asset.asset_key}</td>
                    <td>{asset.kind}</td>
                    <td>{asset.state}</td>
                    <td>{asset.media_type}</td>
                    <td>{new Date(asset.registered_at).toLocaleString("tr-TR")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <aside className={styles.boundary}>
        <strong>Fail-closed production boundary</strong>
        <p>
          Packaged Product Preview media is never a production fallback. READY means only
          operator eligibility for binding; it does not prove upload, malware scan, license,
          provider activation, CDN reachability, SLO or production release.
        </p>
      </aside>
    </main>
  );
}

function TextField({
  label,
  value,
  onChange
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label>
      {label}
      <input value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function AssetDetails({ asset }: { asset: MediaAsset }) {
  return (
    <dl className={styles.details}>
      <div><dt>Asset key</dt><dd>{asset.asset_key}</dd></div>
      <div><dt>State</dt><dd>{asset.state}</dd></div>
      <div><dt>Kind</dt><dd>{asset.kind}</dd></div>
      <div><dt>Delivery ref</dt><dd>{asset.delivery_ref}</dd></div>
      <div><dt>Hash</dt><dd>{asset.content_hash}</dd></div>
      <div><dt>Title</dt><dd>{asset.title}</dd></div>
      <div><dt>Alt text</dt><dd>{asset.alt_text}</dd></div>
      <div><dt>Credit</dt><dd>{asset.credit_label}</dd></div>
      <div><dt>Source</dt><dd>{asset.source_label}</dd></div>
    </dl>
  );
}
