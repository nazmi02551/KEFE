"use client";

import { useMemo, useState } from "react";

import styles from "@/src/components/case-builder-workspace.module.css";
import { AdminApiClient, AdminApiError } from "@/src/lib/admin-api";
import {
  parseJsonSection,
  prettyJson,
  splitLines,
  toDraftInput,
  validateDraft
} from "@/src/lib/case-builder";
import type {
  AdminSession,
  AuthoringAuditEntry,
  CaseBuilderVersion
} from "@/src/lib/contracts";

interface CaseBuilderWorkspaceProps {
  initialVersionId?: string;
}

interface JsonEditors {
  issues: string;
  context_blocks: string;
  sources: string;
  localizations: string;
}

function editorsFor(version: CaseBuilderVersion): JsonEditors {
  return {
    issues: prettyJson(version.issues),
    context_blocks: prettyJson(version.context_blocks),
    sources: prettyJson(version.sources),
    localizations: prettyJson(version.localizations)
  };
}

function messageFor(error: unknown): string {
  if (error instanceof AdminApiError) return `${error.code}: ${error.message}`;
  if (error instanceof Error) return error.message.slice(0, 500);
  return "Beklenmeyen bir hata oluştu.";
}

function statusLabel(state: string): string {
  switch (state) {
    case "DRAFT":
      return "Taslak · düzenlenebilir";
    case "IN_REVIEW":
      return "İncelemede · salt okunur";
    case "APPROVED":
      return "Onaylı · salt okunur";
    case "PUBLISHED":
      return "Yayımlanmış · immutable";
    default:
      return state;
  }
}

export function CaseBuilderWorkspace({
  initialVersionId = ""
}: CaseBuilderWorkspaceProps) {
  const configuredBase = process.env.NEXT_PUBLIC_KEFE_API_BASE_URL ?? "";
  const [apiBaseUrl, setApiBaseUrl] = useState(configuredBase);
  const [csrfToken, setCsrfToken] = useState("");
  const [versionId, setVersionId] = useState(initialVersionId);
  const [session, setSession] = useState<AdminSession | null>(null);
  const [version, setVersion] = useState<CaseBuilderVersion | null>(null);
  const [editors, setEditors] = useState<JsonEditors | null>(null);
  const [audit, setAudit] = useState<AuthoringAuditEntry[]>([]);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [dirty, setDirty] = useState(false);
  const [submitAcknowledged, setSubmitAcknowledged] = useState(false);

  const client = useMemo(
    () => () =>
      new AdminApiClient({
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

  function replaceVersion(next: CaseBuilderVersion, markDirty = true) {
    setVersion(next);
    if (markDirty) setDirty(true);
  }

  function updateField<K extends keyof CaseBuilderVersion>(
    key: K,
    value: CaseBuilderVersion[K]
  ) {
    if (!version) return;
    replaceVersion({ ...version, [key]: value });
  }

  function updateEditor(key: keyof JsonEditors, value: string) {
    if (!editors) return;
    setEditors({ ...editors, [key]: value });
    setDirty(true);
  }

  async function verifySession() {
    await execute(async () => {
      const resolved = await client().session();
      setSession(resolved);
      setFeedback("Admin oturumu doğrulandı.");
    });
  }

  async function loadVersion() {
    const normalized = versionId.trim();
    if (!normalized) {
      setFeedback("Exact CaseVersion ID gereklidir.");
      return;
    }
    await execute(async () => {
      const loaded = await client().caseBuilderVersion(normalized);
      setVersion(loaded);
      setEditors(editorsFor(loaded));
      setAudit([]);
      setDirty(false);
      setSubmitAcknowledged(false);
      setFeedback(`CaseVersion v${loaded.version_no} açık komutla yüklendi.`);
    });
  }

  function materializeEditors(): CaseBuilderVersion {
    if (!version || !editors) throw new Error("Önce bir DRAFT yükleyin.");
    return {
      ...version,
      issues: parseJsonSection("issues", editors.issues),
      context_blocks: parseJsonSection("context_blocks", editors.context_blocks),
      sources: parseJsonSection("sources", editors.sources),
      localizations: parseJsonSection("localizations", editors.localizations)
    } as CaseBuilderVersion;
  }

  async function saveDraft() {
    await execute(async () => {
      const materialized = materializeEditors();
      const problems = validateDraft(materialized);
      if (problems.length > 0) throw new Error(problems.join(" "));
      const saved = await client().saveCaseBuilderDraft(
        materialized.id,
        toDraftInput(materialized)
      );
      setVersion(saved);
      setEditors(editorsFor(saved));
      setDirty(false);
      setSubmitAcknowledged(false);
      setFeedback("DRAFT açık kaydetme komutuyla güncellendi; incelemeye gönderilmedi.");
    });
  }

  async function loadAudit() {
    if (!version) {
      setFeedback("Önce bir CaseVersion yükleyin.");
      return;
    }
    await execute(async () => {
      const trail = await client().caseAudit(version.case_id);
      setAudit(trail.items);
      setFeedback(`${trail.items.length} append-only audit kaydı yüklendi.`);
    });
  }

  async function submitForReview() {
    if (!version) {
      setFeedback("Önce bir DRAFT yükleyin.");
      return;
    }
    if (dirty) {
      setFeedback("Kaydedilmemiş değişiklikler var. Önce DRAFT'ı kaydedin.");
      return;
    }
    if (!submitAcknowledged) {
      setFeedback("İncelemeye gönderme onay kutusunu işaretleyin.");
      return;
    }
    await execute(async () => {
      const submitted = await client().submitCaseVersion(version.id);
      setVersion({ ...version, state: submitted.state });
      setSubmitAcknowledged(false);
      setFeedback("DRAFT ayrı bir komutla IN_REVIEW durumuna gönderildi.");
    });
  }

  const validationProblems = version ? validateDraft(version) : [];
  const editable = version?.state === "DRAFT";

  return (
    <main className={styles.shell}>
      <header className={styles.hero}>
        <div>
          <p className={styles.eyebrow}>KEFE · Admin Studio · CAP-063</p>
          <h1>Case Builder</h1>
          <p>
            Mevcut Content Authoring DRAFT'ını düzenler. Kaydetme ve incelemeye
            gönderme birbirinden ayrı insan komutlarıdır.
          </p>
        </div>
        <a className={styles.backLink} href="/">
          Editoryal operasyonlara dön
        </a>
      </header>

      <section className={styles.connection} aria-labelledby="builder-connection-title">
        <div>
          <h2 id="builder-connection-title">Bağlantı ve exact sürüm</h2>
          <p>Query parametresi yalnız ID'yi doldurur; sayfa açılışında istek yapılmaz.</p>
        </div>
        <label>
          Admin API
          <input
            autoComplete="url"
            onChange={(event) => setApiBaseUrl(event.target.value)}
            placeholder="https://api.example.org"
            type="url"
            value={apiBaseUrl}
          />
        </label>
        <label>
          Aynı oturuma ait CSRF
          <input
            autoComplete="off"
            onChange={(event) => setCsrfToken(event.target.value)}
            placeholder="Yalnız yazma komutları için"
            type="password"
            value={csrfToken}
          />
        </label>
        <button disabled={busy} onClick={verifySession} type="button">
          Oturumu doğrula
        </button>
        <label className={styles.versionField}>
          Exact CaseVersion ID
          <input
            onChange={(event) => setVersionId(event.target.value)}
            placeholder="UUID"
            value={versionId}
          />
        </label>
        <button disabled={busy} onClick={loadVersion} type="button">
          DRAFT'ı açık komutla yükle
        </button>
        {session ? (
          <p className={styles.sessionSummary}>
            Oturum {session.session_id} · {session.roles.join(", ") || "rol yok"}
          </p>
        ) : null}
      </section>

      <div aria-live="polite" className={styles.feedback} role="status">
        {busy ? "İşlem sürüyor…" : feedback}
      </div>

      {version && editors ? (
        <>
          <section className={styles.identityCard} aria-labelledby="version-title">
            <div>
              <p className={styles.eyebrow}>Canonical CaseVersion</p>
              <h2 id="version-title">{version.title}</h2>
              <p className={styles.mono}>{version.id}</p>
            </div>
            <div className={styles.statusStack}>
              <strong data-state={version.state}>{statusLabel(version.state)}</strong>
              <span>
                Case {version.case_id} · v{version.version_no}
              </span>
              <span>{dirty ? "Kaydedilmemiş değişiklik var" : "Sunucuyla eşit"}</span>
            </div>
          </section>

          {validationProblems.length > 0 ? (
            <section className={styles.warning} aria-labelledby="validation-title">
              <h2 id="validation-title">DRAFT doğrulama notları</h2>
              <ul>
                {validationProblems.map((problem) => (
                  <li key={problem}>{problem}</li>
                ))}
              </ul>
            </section>
          ) : null}

          <fieldset className={styles.card} disabled={!editable || busy}>
            <legend>1 · Temel içerik</legend>
            <div className={styles.twoColumns}>
              <label>
                Başlık
                <input
                  onChange={(event) => updateField("title", event.target.value)}
                  value={version.title}
                />
              </label>
              <label>
                Ana alan
                <input
                  onChange={(event) =>
                    updateField("primary_domain_code", event.target.value)
                  }
                  value={version.primary_domain_code}
                />
              </label>
              <label className={styles.fullWidth}>
                Özet
                <textarea
                  onChange={(event) => updateField("summary", event.target.value)}
                  rows={5}
                  value={version.summary}
                />
              </label>
              <label>
                Temel format
                <input
                  onChange={(event) =>
                    updateField("base_format_code", event.target.value)
                  }
                  value={version.base_format_code}
                />
              </label>
              <label>
                İçerik riski
                <input
                  onChange={(event) => updateField("content_risk", event.target.value)}
                  value={version.content_risk}
                />
              </label>
            </div>
          </fieldset>

          <section className={styles.readOnlyCard} aria-labelledby="flow-title">
            <div>
              <p className={styles.eyebrow}>Response-only authority</p>
              <h2 id="flow-title">Flow kimliği</h2>
              <p>Flow topolojisi burada düzenlenmez; CAP-064 ayrı kalır.</p>
            </div>
            <strong>
              {version.flow_template_code} · v{version.flow_template_version_no}
            </strong>
          </section>

          <fieldset className={styles.card} disabled={!editable || busy}>
            <legend>2 · Pazar, dil ve inceleme</legend>
            <div className={styles.twoColumns}>
              <label>
                İçerik dili
                <input
                  onChange={(event) => updateField("content_locale", event.target.value)}
                  value={version.content_locale}
                />
              </label>
              <label>
                Pazar kapsamı
                <select
                  onChange={(event) =>
                    updateField(
                      "market_scope",
                      event.target.value as "GLOBAL" | "COUNTRY_SET"
                    )
                  }
                  value={version.market_scope}
                >
                  <option value="GLOBAL">GLOBAL</option>
                  <option value="COUNTRY_SET">COUNTRY_SET</option>
                </select>
              </label>
              <label>
                Ülke kodları
                <textarea
                  onChange={(event) =>
                    updateField("country_codes", splitLines(event.target.value))
                  }
                  rows={3}
                  value={version.country_codes.join("\n")}
                />
              </label>
              <label>
                Zorunlu inceleme modları
                <textarea
                  onChange={(event) =>
                    updateField(
                      "required_review_modes",
                      splitLines(event.target.value)
                    )
                  }
                  rows={3}
                  value={version.required_review_modes.join("\n")}
                />
              </label>
              <label>
                Modifier kodları
                <textarea
                  onChange={(event) =>
                    updateField("modifiers", splitLines(event.target.value))
                  }
                  rows={3}
                  value={version.modifiers.join("\n")}
                />
              </label>
              <div className={styles.readOnlyField}>
                <span>Tamamlanan incelemeler · server-owned</span>
                <strong>{version.completed_review_modes.join(", ") || "—"}</strong>
              </div>
              <label className={styles.checkboxLabel}>
                <input
                  checked={version.is_fact_bearing}
                  onChange={(event) =>
                    updateField("is_fact_bearing", event.target.checked)
                  }
                  type="checkbox"
                />
                Olgusal iddia içeriyor
              </label>
              <label className={styles.checkboxLabel}>
                <input
                  checked={version.is_real_event}
                  onChange={(event) =>
                    updateField("is_real_event", event.target.checked)
                  }
                  type="checkbox"
                />
                Gerçek olaya dayanıyor
              </label>
              <label className={styles.fullWidth}>
                Kültürel bağlam notu
                <textarea
                  onChange={(event) =>
                    updateField("cultural_context_note", event.target.value || null)
                  }
                  rows={4}
                  value={version.cultural_context_note ?? ""}
                />
              </label>
              <label className={styles.fullWidth}>
                Hukuki bağlam notu
                <textarea
                  onChange={(event) =>
                    updateField("legal_context_note", event.target.value || null)
                  }
                  rows={4}
                  value={version.legal_context_note ?? ""}
                />
              </label>
            </div>
          </fieldset>

          <section className={styles.collectionGrid}>
            <JsonEditor
              disabled={!editable || busy}
              help="Issue, question ve typed response_schema koleksiyonu. UUID ve stable_code değerlerini koruyun."
              label="3 · Meseleler ve sorular"
              onChange={(value) => updateEditor("issues", value)}
              value={editors.issues}
            />
            <JsonEditor
              disabled={!editable || busy}
              help="Kaynak ID bağları ve disclosure/claim durumlarıyla bağlam blokları."
              label="4 · Bağlam blokları"
              onChange={(value) => updateEditor("context_blocks", value)}
              value={editors.context_blocks}
            />
            <JsonEditor
              disabled={!editable || busy}
              help="Yalnız referans metadata'sı; raw evidence ve backend object key burada yoktur."
              label="5 · Kaynak referansları"
              onChange={(value) => updateEditor("sources", value)}
              value={editors.sources}
            />
            <JsonEditor
              disabled={!editable || busy}
              help="Dil bazlı başlık, özet, soru metni ve seçenek etiketleri."
              label="6 · Yerelleştirmeler"
              onChange={(value) => updateEditor("localizations", value)}
              value={editors.localizations}
            />
          </section>

          <section className={styles.actions} aria-labelledby="actions-title">
            <div>
              <h2 id="actions-title">Açık lifecycle komutları</h2>
              <p>Bu yüzeyde approve, reject, publish ve withdraw yoktur.</p>
            </div>
            <button disabled={!editable || busy} onClick={saveDraft} type="button">
              Yalnız DRAFT'ı kaydet
            </button>
            <button disabled={busy} onClick={loadAudit} type="button">
              Audit'i açık komutla yükle
            </button>
            <label className={styles.submitAcknowledge}>
              <input
                checked={submitAcknowledged}
                disabled={!editable || dirty || busy}
                onChange={(event) => setSubmitAcknowledged(event.target.checked)}
                type="checkbox"
              />
              Kaydedilmiş sürümün IN_REVIEW olacağını anlıyorum
            </label>
            <button
              disabled={!editable || dirty || !submitAcknowledged || busy}
              onClick={submitForReview}
              type="button"
            >
              Ayrı komutla incelemeye gönder
            </button>
          </section>

          {audit.length > 0 ? (
            <section className={styles.card} aria-labelledby="audit-title">
              <h2 id="audit-title">Append-only lifecycle audit</h2>
              <div className={styles.tableWrap}>
                <table>
                  <thead>
                    <tr>
                      <th>Komut</th>
                      <th>Geçiş</th>
                      <th>Aktör</th>
                      <th>Zaman</th>
                    </tr>
                  </thead>
                  <tbody>
                    {audit.map((entry) => (
                      <tr key={entry.audit_id}>
                        <td>{entry.command}</td>
                        <td>
                          {entry.previous_state ?? "∅"} → {entry.new_state}
                        </td>
                        <td className={styles.mono}>{entry.actor_ref}</td>
                        <td>{new Date(entry.occurred_at).toLocaleString("tr-TR")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          ) : null}
        </>
      ) : (
        <section className={styles.emptyState}>
          <h2>Henüz CaseVersion yüklenmedi</h2>
          <p>
            Exact ID'yi girin ve yükleme düğmesine basın. Bu boş durum herhangi bir
            API isteği veya mutasyon başlatmaz.
          </p>
        </section>
      )}
    </main>
  );
}

function JsonEditor({
  label,
  help,
  value,
  onChange,
  disabled
}: {
  label: string;
  help: string;
  value: string;
  onChange: (value: string) => void;
  disabled: boolean;
}) {
  return (
    <section className={styles.jsonCard}>
      <h2>{label}</h2>
      <p>{help}</p>
      <textarea
        aria-label={label}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        rows={16}
        spellCheck={false}
        value={value}
      />
    </section>
  );
}
