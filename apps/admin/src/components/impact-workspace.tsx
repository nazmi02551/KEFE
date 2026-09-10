"use client";

/**
 * Impact Workspace — Admin Studio
 *
 * Shows institution responses (read-only) and action milestones (read/write).
 * Impact follows Signal; Signal follows methodology-qualified Collective Result.
 * Admin Studio does not create institution responses — those are ingested
 * through the authority verification pipeline.
 *
 * Design system: dark-first, gold accent, semantic surfaces.
 */

import { useEffect, useState } from "react";
import styles from "@/src/components/impact-workspace.module.css";
import type { ActionMilestone, InstitutionResponse } from "@/src/lib/impact-api";
import {
  listActionMilestones,
  listInstitutionResponses,
  proposeAction,
  updateActionProgress,
} from "@/src/lib/impact-api";

const RESPONSE_TYPE_LABELS: Record<string, string> = {
  ACKNOWLEDGE: "Alındı",
  COMMITMENT: "Taahhüt",
  POLICY_CHANGE: "Politika Değişikliği",
  FACTUAL_CLARIFICATION: "Bilgi Tashihi",
  DECLINE_WITH_REASON: "Gerekçeli Red",
};

const ACTION_STATUS_LABELS: Record<string, string> = {
  PROPOSED: "Önerildi",
  IN_PROGRESS: "Devam Ediyor",
  VERIFIED_COMPLETE: "Tamamlandı",
  STALLED: "Askıya Alındı",
};

const ACTION_STATUS_CLASS: Record<string, string> = {
  PROPOSED: styles.statusProposed,
  IN_PROGRESS: styles.statusInProgress,
  VERIFIED_COMPLETE: styles.statusComplete,
  STALLED: styles.statusStalled,
};

interface ImpactWorkspaceProps {
  baseUrl: string;
  csrfToken: string;
  caseVersionId?: string;
}

export function ImpactWorkspace({ baseUrl, csrfToken, caseVersionId }: ImpactWorkspaceProps) {
  const [responses, setResponses] = useState<InstitutionResponse[]>([]);
  const [actions, setActions] = useState<ActionMilestone[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [proposing, setProposing] = useState(false);
  const [proposeError, setProposeError] = useState<string | null>(null);

  const [proposeTitle, setProposeTitle] = useState("");
  const [proposeDescription, setProposeDescription] = useState("");
  const [proposeCaseId, setProposeCaseId] = useState(caseVersionId ?? "");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const [resps, acts] = await Promise.all([
          listInstitutionResponses(baseUrl, { caseVersionId, limit: 50 }),
          listActionMilestones(baseUrl, { caseVersionId, limit: 50 }),
        ]);
        if (!cancelled) {
          setResponses(resps);
          setActions(acts);
        }
      } catch (err) {
        if (!cancelled) setError((err as Error).message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, [baseUrl, caseVersionId]);

  async function handleProposeAction(e: React.FormEvent) {
    e.preventDefault();
    setProposing(true);
    setProposeError(null);
    try {
      const action = await proposeAction(
        baseUrl,
        {
          case_version_id: proposeCaseId,
          title: proposeTitle,
          description: proposeDescription,
        },
        csrfToken
      );
      setActions((prev) => [action, ...prev]);
      setProposeTitle("");
      setProposeDescription("");
    } catch (err: unknown) {
      setProposeError(err instanceof Error ? err.message : "Bilinmeyen hata");
    } finally {
      setProposing(false);
    }
  }

  async function handleProgressUpdate(
    action: ActionMilestone,
    newStatus: ActionMilestone["status"],
    newProgress: number
  ) {
    try {
      const updated = await updateActionProgress(
        baseUrl,
        action.action_id,
        {
          case_version_id: action.case_version_id,
          progress_percentage: newProgress,
          status: newStatus,
        },
        csrfToken
      );
      setActions((prev) =>
        prev.map((a) => (a.action_id === updated.action_id ? updated : a))
      );
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "İlerleme güncellenemedi");
    }
  }

  if (loading) {
    return (
      <div className={styles.workspace}>
        <p className={styles.loadingText} role="status" aria-live="polite">
          Etki verileri yükleniyor…
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.workspace}>
        <p className={styles.errorText} role="alert">
          {error}
        </p>
      </div>
    );
  }

  return (
    <div className={styles.workspace}>
      <header className={styles.workspaceHeader}>
        <h1 className={styles.title}>Etki Takip Merkezi</h1>
        <p className={styles.subtitle}>
          Kurum yanıtları ve eylem kilometre taşları. Etki, nitelikli sinyal üzerine inşa
          edilir; sinyal otomatik olarak etki anlamına gelmez.
        </p>
      </header>

      {/* Institution Responses */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>
          Kurum Yanıtları
          <span className={styles.sectionCount}>({responses.length})</span>
        </h2>
        {responses.length === 0 ? (
          <p className={styles.emptyText}>Henüz doğrulanmış kurum yanıtı bulunmuyor.</p>
        ) : (
          <ul className={styles.responseList} aria-label="Kurum yanıtları">
            {responses.map((r) => (
              <li key={r.response_id} className={styles.responseCard}>
                <div className={styles.responseHeader}>
                  <span className={styles.institutionName}>{r.institution_name}</span>
                  <span className={styles.responseTypeBadge}>
                    {RESPONSE_TYPE_LABELS[r.response_type] ?? r.response_type}
                  </span>
                </div>
                <p className={styles.authorityRole}>{r.authority_role}</p>
                <p className={styles.statement}>{r.statement}</p>
                <time className={styles.publishedAt} dateTime={r.published_at}>
                  {new Date(r.published_at).toLocaleDateString("tr-TR")}
                </time>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Propose Action Form */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Yeni Eylem Öner</h2>
        <form className={styles.proposeForm} onSubmit={handleProposeAction} noValidate>
          {!caseVersionId && (
            <div className={styles.field}>
              <label htmlFor="propose-case-id" className={styles.label}>
                Dava ID (UUID)
              </label>
              <input
                id="propose-case-id"
                type="text"
                className={styles.input}
                value={proposeCaseId}
                onChange={(e) => setProposeCaseId(e.target.value)}
                placeholder="22222222-2222-4222-8222-222222222222"
                required
                pattern="[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
              />
            </div>
          )}
          <div className={styles.field}>
            <label htmlFor="propose-title" className={styles.label}>
              Başlık <span className={styles.required}>*</span>
            </label>
            <input
              id="propose-title"
              type="text"
              className={styles.input}
              value={proposeTitle}
              onChange={(e) => setProposeTitle(e.target.value)}
              placeholder="Eylem başlığını girin (en az 3 karakter)"
              required
              minLength={3}
              maxLength={200}
            />
          </div>
          <div className={styles.field}>
            <label htmlFor="propose-desc" className={styles.label}>
              Açıklama <span className={styles.required}>*</span>
            </label>
            <textarea
              id="propose-desc"
              className={styles.textarea}
              value={proposeDescription}
              onChange={(e) => setProposeDescription(e.target.value)}
              placeholder="Eylem planını detaylı açıklayın (en az 10 karakter)"
              required
              minLength={10}
              maxLength={2000}
              rows={4}
            />
          </div>
          {proposeError && (
            <p className={styles.formError} role="alert">
              {proposeError}
            </p>
          )}
          <button
            type="submit"
            className={styles.submitButton}
            disabled={proposing}
          >
            {proposing ? "Kaydediliyor…" : "Eylem Öner"}
          </button>
        </form>
      </section>

      {/* Action Milestones */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>
          Eylem Kilometre Taşları
          <span className={styles.sectionCount}>({actions.length})</span>
        </h2>
        {actions.length === 0 ? (
          <p className={styles.emptyText}>Henüz bir eylem kilometre taşı bulunmuyor.</p>
        ) : (
          <ul className={styles.actionList} aria-label="Eylem listesi">
            {actions.map((a) => (
              <li key={a.action_id} className={styles.actionCard}>
                <div className={styles.actionHeader}>
                  <h3 className={styles.actionTitle}>{a.title}</h3>
                  <span
                    className={`${styles.statusBadge} ${ACTION_STATUS_CLASS[a.status] ?? ""}`}
                  >
                    {ACTION_STATUS_LABELS[a.status] ?? a.status}
                  </span>
                </div>
                <p className={styles.actionDesc}>{a.description}</p>
                <div className={styles.progressRow}>
                  <div className={styles.progressBar} role="progressbar"
                    aria-valuenow={a.progress_percentage}
                    aria-valuemin={0}
                    aria-valuemax={100}
                  >
                    <div
                      className={styles.progressFill}
                      style={{ width: `${a.progress_percentage}%` }}
                    />
                  </div>
                  <span className={styles.progressLabel}>%{a.progress_percentage}</span>
                </div>
                {a.evidence_url && (
                  <a
                    href={a.evidence_url}
                    className={styles.evidenceLink}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Kanıtı İncele →
                  </a>
                )}
                <div className={styles.actionActions}>
                  {a.status !== "VERIFIED_COMPLETE" && a.status !== "STALLED" && (
                    <button
                      type="button"
                      className={styles.progressButton}
                      onClick={() =>
                        handleProgressUpdate(a, "IN_PROGRESS", Math.min(a.progress_percentage + 25, 100))
                      }
                    >
                      +25% İlerleme
                    </button>
                  )}
                  {a.status === "IN_PROGRESS" && a.progress_percentage >= 100 && (
                    <button
                      type="button"
                      className={styles.completeButton}
                      onClick={() => handleProgressUpdate(a, "VERIFIED_COMPLETE", 100)}
                    >
                      Tamamlandı olarak işaretle
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}