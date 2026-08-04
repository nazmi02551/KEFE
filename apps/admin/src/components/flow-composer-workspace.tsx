"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import styles from "@/src/components/flow-composer-workspace.module.css";
import { AdminApiClient, AdminApiError } from "@/src/lib/admin-api";
import type { AdminSession } from "@/src/lib/contracts";
import {
  createFlowStep,
  createFlowTemplate,
  moveItem,
  parseCodeList,
  topologyPreview,
  validateFlowComposerVersion
} from "@/src/lib/flow-composer";
import type {
  ConfigurationAuditEntry,
  FlowComposerStep,
  FlowComposerTemplate,
  FlowComposerVersion
} from "@/src/lib/flow-composer";

interface FlowComposerWorkspaceProps {
  initialVersionId?: string;
}

function cloneVersion(version: FlowComposerVersion): FlowComposerVersion {
  return {
    ...version,
    primitives: version.primitives.map((item) => ({ ...item })),
    capabilities: version.capabilities.map((item) => ({
      ...item,
      compatible_primitive_codes: [...item.compatible_primitive_codes]
    })),
    flow_templates: version.flow_templates.map((flow) => ({
      ...flow,
      steps: flow.steps.map((step) => ({
        ...step,
        capability_codes: [...step.capability_codes],
        next_step_codes: [...step.next_step_codes]
      }))
    }))
  };
}

function messageFor(error: unknown): string {
  if (error instanceof AdminApiError) return `${error.code}: ${error.message}`;
  if (error instanceof Error) return error.message.replace(/\s+/g, " ").slice(0, 500);
  return "Beklenmeyen bir hata oluştu.";
}

function formattedDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString("tr-TR");
}

function updateAt<T>(items: T[], index: number, value: T): T[] {
  return items.map((item, currentIndex) => (currentIndex === index ? value : item));
}

export function FlowComposerWorkspace({
  initialVersionId = ""
}: FlowComposerWorkspaceProps) {
  const configuredBase = process.env.NEXT_PUBLIC_KEFE_API_BASE_URL ?? "";
  const [apiBaseUrl, setApiBaseUrl] = useState(configuredBase);
  const [csrfToken, setCsrfToken] = useState("");
  const [versionId, setVersionId] = useState(initialVersionId);
  const [session, setSession] = useState<AdminSession | null>(null);
  const [version, setVersion] = useState<FlowComposerVersion | null>(null);
  const [baseline, setBaseline] = useState<FlowComposerVersion | null>(null);
  const [audit, setAudit] = useState<ConfigurationAuditEntry[]>([]);
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState("");

  const client = useMemo(
    () => () => new AdminApiClient({ baseUrl: apiBaseUrl, csrfToken }),
    [apiBaseUrl, csrfToken]
  );

  const validationProblems = version ? validateFlowComposerVersion(version) : [];
  const editable = version?.state === "DRAFT";

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

  function installVersion(next: FlowComposerVersion) {
    const clean = cloneVersion(next);
    setVersion(clean);
    setBaseline(cloneVersion(next));
    setVersionId(next.id);
    setAudit([]);
    setDirty(false);
  }

  function replaceFlows(flowTemplates: FlowComposerTemplate[]) {
    if (!version || !editable) return;
    setVersion({ ...version, flow_templates: flowTemplates });
    setDirty(true);
  }

  async function verifySession() {
    await execute(async () => {
      const resolved = await client().session();
      setSession(resolved);
      setFeedback("Taxonomy Manager oturumu açık komutla doğrulandı.");
    });
  }

  async function createDraft() {
    if (dirty) {
      setFeedback("Kaydedilmemiş değişiklikler var. Önce kaydedin veya geri alın.");
      return;
    }
    await execute(async () => {
      const created = await client().createFlowComposerDraft();
      installVersion(created);
      setFeedback(
        `Content Configuration v${created.version_no} DRAFT olarak klonlandı; yayımlanmadı.`
      );
    });
  }

  async function loadVersion() {
    if (dirty) {
      setFeedback("Kaydedilmemiş değişiklikler var. Önce kaydedin veya geri alın.");
      return;
    }
    const normalized = versionId.trim();
    if (!normalized) {
      setFeedback("Exact Content Configuration version ID gereklidir.");
      return;
    }
    await execute(async () => {
      const loaded = await client().flowComposerVersion(normalized);
      installVersion(loaded);
      setFeedback(
        `Configuration v${loaded.version_no} açık komutla yüklendi. ${
          loaded.state === "DRAFT" ? "Düzenlenebilir." : "Salt okunur."
        }`
      );
    });
  }

  async function saveVersion() {
    if (!version) {
      setFeedback("Önce bir Content Configuration DRAFT yükleyin.");
      return;
    }
    if (!editable) {
      setFeedback("Yalnız DRAFT configuration sürümleri Flow Composer ile kaydedilebilir.");
      return;
    }
    if (validationProblems.length > 0) {
      setFeedback(validationProblems.slice(0, 5).join(" "));
      return;
    }
    await execute(async () => {
      const saved = await client().saveFlowComposerVersion(version.id, {
        flow_templates: version.flow_templates
      });
      installVersion(saved);
      setFeedback("Flow şablonları DRAFT içinde kaydedildi; yayın ve runtime değişmedi.");
    });
  }

  async function loadAudit() {
    if (!version) {
      setFeedback("Önce bir configuration sürümü yükleyin.");
      return;
    }
    await execute(async () => {
      const trail = await client().flowComposerAudit(version.id);
      setAudit(trail.items);
      setFeedback(`${trail.items.length} append-only configuration audit kaydı yüklendi.`);
    });
  }

  function discardChanges() {
    if (!baseline) return;
    setVersion(cloneVersion(baseline));
    setDirty(false);
    setFeedback("Kaydedilmemiş Flow değişiklikleri geri alındı.");
  }

  function addFlow() {
    if (!version || !editable) return;
    replaceFlows([
      ...version.flow_templates,
      createFlowTemplate(version.flow_templates.length + 1)
    ]);
  }

  function removeFlow(flowIndex: number) {
    if (!version || !editable) return;
    replaceFlows(version.flow_templates.filter((_, index) => index !== flowIndex));
  }

  function moveFlow(flowIndex: number, direction: -1 | 1) {
    if (!version || !editable) return;
    replaceFlows(moveItem(version.flow_templates, flowIndex, flowIndex + direction));
  }

  function updateFlow(flowIndex: number, next: FlowComposerTemplate) {
    if (!version || !editable) return;
    replaceFlows(updateAt(version.flow_templates, flowIndex, next));
  }

  function addStep(flowIndex: number) {
    const flow = version?.flow_templates[flowIndex];
    if (!flow || !editable) return;
    updateFlow(flowIndex, {
      ...flow,
      steps: [...flow.steps, createFlowStep(flow.steps.length + 1)]
    });
  }

  function removeStep(flowIndex: number, stepIndex: number) {
    const flow = version?.flow_templates[flowIndex];
    if (!flow || !editable) return;
    updateFlow(flowIndex, {
      ...flow,
      steps: flow.steps.filter((_, index) => index !== stepIndex)
    });
  }

  function moveStep(flowIndex: number, stepIndex: number, direction: -1 | 1) {
    const flow = version?.flow_templates[flowIndex];
    if (!flow || !editable) return;
    updateFlow(flowIndex, {
      ...flow,
      steps: moveItem(flow.steps, stepIndex, stepIndex + direction)
    });
  }

  function updateStep(
    flowIndex: number,
    stepIndex: number,
    next: FlowComposerStep
  ) {
    const flow = version?.flow_templates[flowIndex];
    if (!flow || !editable) return;
    updateFlow(flowIndex, {
      ...flow,
      steps: updateAt(flow.steps, stepIndex, next)
    });
  }

  return (
    <main className={styles.shell}>
      <header className={styles.hero}>
        <div>
          <p className={styles.eyebrow}>KEFE · Admin Studio · CAP-064</p>
          <h1>Flow Composer</h1>
          <p>
            Generic Flow şablonlarını mevcut Content Configuration DRAFT içinde
            düzenler. Kaydetme hiçbir configuration yayınlamaz ve consumer runtime’ı
            değiştirmez.
          </p>
        </div>
        <Link className={styles.backLink} href="/">
          Editoryal operasyonlara dön
        </Link>
      </header>

      <section className={styles.boundary} aria-label="Flow Composer sınırı">
        <strong>DRAFT-only sınır</strong>
        <span>
          Primitive ve Capability katalogları salt okunur. Yalnız flow_templates
          gönderilir; diğer configuration alanları sunucuda korunur.
        </span>
      </section>

      <section className={styles.connection} aria-labelledby="connection-title">
        <div>
          <p className={styles.sectionLabel}>Bağlantı</p>
          <h2 id="connection-title">Açık operatör komutları</h2>
        </div>
        <label>
          Admin API base URL
          <input
            disabled={busy}
            inputMode="url"
            onChange={(event) => setApiBaseUrl(event.target.value)}
            placeholder="https://api.example.com"
            value={apiBaseUrl}
          />
        </label>
        <label>
          Aynı oturum CSRF
          <input
            autoComplete="off"
            disabled={busy}
            onChange={(event) => setCsrfToken(event.target.value)}
            type="password"
            value={csrfToken}
          />
        </label>
        <div className={styles.commandRow}>
          <button disabled={busy} onClick={verifySession} type="button">
            Oturumu doğrula
          </button>
          <button disabled={busy || dirty} onClick={createDraft} type="button">
            Current’tan yeni DRAFT oluştur
          </button>
        </div>
        {session ? (
          <p className={styles.sessionSummary}>
            {session.admin_subject_id} · {session.roles.join(", ") || "rol yok"}
          </p>
        ) : null}
      </section>

      <section className={styles.loader} aria-labelledby="loader-title">
        <div>
          <p className={styles.sectionLabel}>Exact version</p>
          <h2 id="loader-title">Configuration sürümünü yükle</h2>
        </div>
        <label className={styles.grow}>
          Version ID
          <input
            disabled={busy}
            onChange={(event) => setVersionId(event.target.value)}
            placeholder="UUID"
            value={versionId}
          />
        </label>
        <button disabled={busy || dirty} onClick={loadVersion} type="button">
          Açık komutla yükle
        </button>
      </section>

      {feedback ? (
        <p aria-live="polite" className={styles.feedback} role="status">
          {feedback}
        </p>
      ) : null}

      {version ? (
        <>
          <section className={styles.versionHeader} aria-label="Configuration kimliği">
            <div>
              <p className={styles.sectionLabel}>Content Configuration</p>
              <h2>v{version.version_no}</h2>
              <code>{version.id}</code>
            </div>
            <dl>
              <div>
                <dt>Durum</dt>
                <dd>{version.state}</dd>
              </div>
              <div>
                <dt>Kaynak sürüm</dt>
                <dd>{version.cloned_from_version_id ?? "—"}</dd>
              </div>
              <div>
                <dt>Oluşturulma</dt>
                <dd>{formattedDate(version.created_at)}</dd>
              </div>
            </dl>
          </section>

          <section className={styles.catalogGrid} aria-label="Salt okunur kataloglar">
            <article className={styles.catalogCard}>
              <p className={styles.sectionLabel}>Salt okunur</p>
              <h2>Primitive kataloğu</h2>
              <ul>
                {version.primitives.map((primitive) => (
                  <li key={primitive.code}>
                    <code>{primitive.code}</code>
                    <span>{primitive.label_key}</span>
                    <small>{primitive.enabled ? "enabled" : "disabled"}</small>
                  </li>
                ))}
              </ul>
            </article>
            <article className={styles.catalogCard}>
              <p className={styles.sectionLabel}>Salt okunur</p>
              <h2>Capability kataloğu</h2>
              <ul>
                {version.capabilities.map((capability) => (
                  <li key={capability.code}>
                    <code>{capability.code}</code>
                    <span>
                      {capability.compatible_primitive_codes.join(", ") ||
                        "tüm Primitive’ler"}
                    </span>
                    <small>{capability.enabled ? "enabled" : "disabled"}</small>
                  </li>
                ))}
              </ul>
            </article>
          </section>

          <section className={styles.editorHeader}>
            <div>
              <p className={styles.sectionLabel}>Versioned generic graph</p>
              <h2>Flow şablonları</h2>
              <p>{version.flow_templates.length} şablon · {dirty ? "kaydedilmemiş değişiklik" : "temiz"}</p>
            </div>
            <button disabled={!editable || busy} onClick={addFlow} type="button">
              Flow ekle
            </button>
          </section>

          <div className={styles.flowList}>
            {version.flow_templates.map((flow, flowIndex) => (
              <article className={styles.flowCard} key={`${flow.code}-${flow.version_no}-${flowIndex}`}>
                <header className={styles.flowCardHeader}>
                  <div>
                    <p className={styles.sectionLabel}>Flow {flowIndex + 1}</p>
                    <h3>{flow.code || "Yeni Flow"} · v{flow.version_no}</h3>
                  </div>
                  <div className={styles.compactCommands}>
                    <button
                      aria-label="Flow'u yukarı taşı"
                      disabled={!editable || busy || flowIndex === 0}
                      onClick={() => moveFlow(flowIndex, -1)}
                      type="button"
                    >
                      ↑
                    </button>
                    <button
                      aria-label="Flow'u aşağı taşı"
                      disabled={
                        !editable ||
                        busy ||
                        flowIndex === version.flow_templates.length - 1
                      }
                      onClick={() => moveFlow(flowIndex, 1)}
                      type="button"
                    >
                      ↓
                    </button>
                    <button
                      className={styles.dangerButton}
                      disabled={!editable || busy}
                      onClick={() => removeFlow(flowIndex)}
                      type="button"
                    >
                      Flow’u kaldır
                    </button>
                  </div>
                </header>

                <div className={styles.flowFields}>
                  <label>
                    Flow code
                    <input
                      disabled={!editable || busy}
                      onChange={(event) =>
                        updateFlow(flowIndex, { ...flow, code: event.target.value })
                      }
                      value={flow.code}
                    />
                  </label>
                  <label>
                    Version no
                    <input
                      disabled={!editable || busy}
                      min={1}
                      onChange={(event) =>
                        updateFlow(flowIndex, {
                          ...flow,
                          version_no: Number(event.target.value)
                        })
                      }
                      type="number"
                      value={flow.version_no}
                    />
                  </label>
                  <label>
                    Label key
                    <input
                      disabled={!editable || busy}
                      onChange={(event) =>
                        updateFlow(flowIndex, { ...flow, label_key: event.target.value })
                      }
                      value={flow.label_key}
                    />
                  </label>
                  <label>
                    Entry Step code
                    <input
                      disabled={!editable || busy}
                      onChange={(event) =>
                        updateFlow(flowIndex, {
                          ...flow,
                          entry_step_code: event.target.value
                        })
                      }
                      value={flow.entry_step_code}
                    />
                  </label>
                  <label className={styles.checkboxLabel}>
                    <input
                      checked={flow.enabled}
                      disabled={!editable || busy}
                      onChange={(event) =>
                        updateFlow(flowIndex, { ...flow, enabled: event.target.checked })
                      }
                      type="checkbox"
                    />
                    Enabled Flow
                  </label>
                </div>

                <div className={styles.stepsHeader}>
                  <h4>Step’ler</h4>
                  <button
                    disabled={!editable || busy}
                    onClick={() => addStep(flowIndex)}
                    type="button"
                  >
                    Step ekle
                  </button>
                </div>

                <div className={styles.stepList}>
                  {flow.steps.map((step, stepIndex) => (
                    <section className={styles.stepCard} key={`${step.code}-${stepIndex}`}>
                      <header>
                        <strong>Step {stepIndex + 1}</strong>
                        <div className={styles.compactCommands}>
                          <button
                            aria-label="Step'i yukarı taşı"
                            disabled={!editable || busy || stepIndex === 0}
                            onClick={() => moveStep(flowIndex, stepIndex, -1)}
                            type="button"
                          >
                            ↑
                          </button>
                          <button
                            aria-label="Step'i aşağı taşı"
                            disabled={
                              !editable || busy || stepIndex === flow.steps.length - 1
                            }
                            onClick={() => moveStep(flowIndex, stepIndex, 1)}
                            type="button"
                          >
                            ↓
                          </button>
                          <button
                            className={styles.dangerButton}
                            disabled={!editable || busy}
                            onClick={() => removeStep(flowIndex, stepIndex)}
                            type="button"
                          >
                            Kaldır
                          </button>
                        </div>
                      </header>
                      <div className={styles.stepFields}>
                        <label>
                          Step code
                          <input
                            disabled={!editable || busy}
                            onChange={(event) =>
                              updateStep(flowIndex, stepIndex, {
                                ...step,
                                code: event.target.value
                              })
                            }
                            value={step.code}
                          />
                        </label>
                        <label>
                          Primitive
                          <select
                            disabled={!editable || busy}
                            onChange={(event) =>
                              updateStep(flowIndex, stepIndex, {
                                ...step,
                                primitive_code: event.target.value
                              })
                            }
                            value={step.primitive_code}
                          >
                            {version.primitives.map((primitive) => (
                              <option key={primitive.code} value={primitive.code}>
                                {primitive.code}{primitive.enabled ? "" : " · disabled"}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label>
                          Capability codes · virgülle
                          <input
                            disabled={!editable || busy}
                            onChange={(event) =>
                              updateStep(flowIndex, stepIndex, {
                                ...step,
                                capability_codes: parseCodeList(event.target.value)
                              })
                            }
                            value={step.capability_codes.join(", ")}
                          />
                        </label>
                        <label>
                          Next Step codes · virgülle
                          <input
                            disabled={!editable || busy}
                            onChange={(event) =>
                              updateStep(flowIndex, stepIndex, {
                                ...step,
                                next_step_codes: parseCodeList(event.target.value)
                              })
                            }
                            value={step.next_step_codes.join(", ")}
                          />
                        </label>
                        <label className={styles.wideField}>
                          Payload schema ref
                          <input
                            disabled={!editable || busy}
                            onChange={(event) =>
                              updateStep(flowIndex, stepIndex, {
                                ...step,
                                payload_schema_ref: event.target.value.trim() || null
                              })
                            }
                            value={step.payload_schema_ref ?? ""}
                          />
                        </label>
                      </div>
                    </section>
                  ))}
                </div>

                <section className={styles.topology} aria-label={`${flow.code} topoloji önizlemesi`}>
                  <h4>Deterministik topoloji</h4>
                  <ol>
                    {topologyPreview(flow).map((line, index) => (
                      <li key={`${line}-${index}`}><code>{line}</code></li>
                    ))}
                  </ol>
                </section>
              </article>
            ))}
          </div>

          <section className={styles.validation} aria-live="polite">
            <div>
              <p className={styles.sectionLabel}>Pre-save kontrol</p>
              <h2>
                {validationProblems.length === 0
                  ? "İstemci graph kontrolü temiz"
                  : `${validationProblems.length} sorun bulundu`}
              </h2>
            </div>
            {validationProblems.length > 0 ? (
              <ul>
                {validationProblems.map((problem) => (
                  <li key={problem}>{problem}</li>
                ))}
              </ul>
            ) : (
              <p>Sunucu doğrulaması yine nihai otoritedir.</p>
            )}
          </section>

          <section className={styles.finalCommands}>
            <button
              disabled={!editable || busy || !dirty || validationProblems.length > 0}
              onClick={saveVersion}
              type="button"
            >
              DRAFT Flow’larını kaydet
            </button>
            <button disabled={!dirty || busy} onClick={discardChanges} type="button">
              Kaydedilmemiş değişiklikleri geri al
            </button>
            <button disabled={busy} onClick={loadAudit} type="button">
              Audit’i açık komutla yükle
            </button>
          </section>

          {audit.length > 0 ? (
            <section className={styles.audit} aria-labelledby="audit-title">
              <p className={styles.sectionLabel}>Append-only</p>
              <h2 id="audit-title">Configuration audit</h2>
              <ol>
                {audit.map((entry) => (
                  <li key={entry.audit_id}>
                    <strong>{entry.command}</strong>
                    <span>{entry.previous_state ?? "∅"} → {entry.new_state}</span>
                    <small>{entry.actor_ref} · {formattedDate(entry.occurred_at)}</small>
                  </li>
                ))}
              </ol>
            </section>
          ) : null}
        </>
      ) : (
        <section className={styles.emptyState}>
          <h2>Henüz configuration yüklenmedi</h2>
          <p>
            Query parametresi yalnız ID alanını doldurur. Ağ isteği için yukarıdaki
            açık komutlardan birini kullanın.
          </p>
        </section>
      )}
    </main>
  );
}
