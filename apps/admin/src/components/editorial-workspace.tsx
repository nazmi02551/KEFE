"use client";

import { FormEvent, useMemo, useState } from "react";

import {
  StatusBadge,
  WorkspaceStage,
  WorkspaceStepper
} from "@/src/components/workspace-primitives";
import { AdminApiClient, AdminApiError } from "@/src/lib/admin-api";
import type {
  AdminSession,
  CandidateBundleRequest,
  CandidateBundleResponse,
  EditorialProjectionResponse,
  ProposalDetail,
  ProposalQueueItem,
  ProposalReviewDecision,
  ProposalReviewResponse,
  ProposalReviewState
} from "@/src/lib/contracts";
import { projectionIdempotencyKey } from "@/src/lib/idempotency";

const defaultBundle: CandidateBundleRequest = {
  source_brief_review_decision_id: "",
  slug: "",
  title: "",
  summary: "",
  base_format_code: "STANDARD_CASE",
  primary_domain_code: "PUBLIC_LIFE",
  content_risk: "MEDIUM",
  issue_code: "primary-issue",
  issue_title: "Ana mesele",
  question_stable_code: "primary-question",
  question_prompt: "Bu durumda en adil karar hangisidir?",
  response_options: ["Katılıyorum", "Katılmıyorum"],
  flow_template_code: "STANDARD_WEIGH",
  flow_template_version_no: 1,
  content_locale: "tr",
  market_scope: "GLOBAL",
  country_codes: [],
  required_review_modes: ["EDITORIAL", "FACT_CHECK"],
  is_fact_bearing: true,
  is_real_event: true,
  context_title: "Bağlam",
  cultural_context_note: null,
  legal_context_note: null
};

function splitList(value: string): string[] {
  return value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function messageFor(error: unknown): string {
  if (error instanceof AdminApiError) return `${error.code}: ${error.message}`;
  if (error instanceof Error) return error.message.slice(0, 500);
  return "Beklenmeyen bir hata oluştu";
}

function Metadata({ proposal }: { proposal: ProposalQueueItem }) {
  return (
    <dl className="metadataGrid">
      <div>
        <dt>Proposal</dt>
        <dd>{proposal.proposal_id}</dd>
      </div>
      <div>
        <dt>Tür</dt>
        <dd>{proposal.proposal_kind}</dd>
      </div>
      <div>
        <dt>Pipeline</dt>
        <dd>
          {proposal.pipeline_code} / {proposal.pipeline_version}
        </dd>
      </div>
      <div>
        <dt>Risk</dt>
        <dd>{proposal.risk_code ?? "—"}</dd>
      </div>
      <div>
        <dt>Run</dt>
        <dd>{proposal.run_id}</dd>
      </div>
      <div>
        <dt>Girdi</dt>
        <dd>
          {proposal.input_artifact_kind} / {proposal.input_artifact_id}
        </dd>
      </div>
    </dl>
  );
}

export function EditorialWorkspace() {
  const configuredBase = process.env.NEXT_PUBLIC_KEFE_API_BASE_URL ?? "";
  const [apiBaseUrl, setApiBaseUrl] = useState(configuredBase);
  const [csrfToken, setCsrfToken] = useState("");
  const [stage, setStage] = useState<WorkspaceStage>("QUEUE");
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [session, setSession] = useState<AdminSession | null>(null);
  const [queue, setQueue] = useState<ProposalQueueItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [reviewState, setReviewState] = useState<ProposalReviewState | "">("PENDING");
  const [proposalKind, setProposalKind] = useState("");
  const [riskCode, setRiskCode] = useState("");
  const [pipelineCode, setPipelineCode] = useState("");
  const [selected, setSelected] = useState<ProposalDetail | null>(null);
  const [decision, setDecision] = useState<ProposalReviewDecision>("ACCEPTED");
  const [rationale, setRationale] = useState("");
  const [reasonCode, setReasonCode] = useState("");
  const [policyVersion, setPolicyVersion] = useState("");
  const [riskPolicyVersion, setRiskPolicyVersion] = useState("");
  const [lastReview, setLastReview] = useState<ProposalReviewResponse | null>(null);
  const [bundle, setBundle] = useState<CandidateBundleRequest>(defaultBundle);
  const [bundleResult, setBundleResult] = useState<CandidateBundleResponse | null>(null);
  const [candidateProposalId, setCandidateProposalId] = useState("");
  const [candidateReviewDecisionId, setCandidateReviewDecisionId] = useState("");
  const [profileCode, setProfileCode] = useState("STANDARD_EDITORIAL");
  const [profileVersion, setProfileVersion] = useState(1);
  const [idempotencyKey, setIdempotencyKey] = useState("");
  const [projectionResult, setProjectionResult] =
    useState<EditorialProjectionResponse | null>(null);

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

  async function verifySession() {
    await execute(async () => {
      const resolved = await client().session();
      setSession(resolved);
      setFeedback("Admin oturumu doğrulandı.");
    });
  }

  async function loadQueue(cursor?: string) {
    await execute(async () => {
      const page = await client().proposals({
        limit: 25,
        cursor,
        review_state: reviewState || undefined,
        proposal_kind: proposalKind || undefined,
        risk_code: riskCode || undefined,
        pipeline_code: pipelineCode || undefined
      });
      setQueue(page.items);
      setNextCursor(page.next_cursor);
      setFeedback(`${page.items.length} kayıt yüklendi.`);
    });
  }

  async function selectProposal(proposalId: string) {
    await execute(async () => {
      const detail = await client().proposal(proposalId);
      setSelected(detail);
      setLastReview(null);
      if (detail.proposal_kind === "SOURCE_BRIEF" && detail.review) {
        setBundle((current) => ({
          ...current,
          source_brief_review_decision_id:
            detail.review?.proposal_review_decision_id ?? ""
        }));
      }
      setStage("REVIEW");
      setFeedback("Proposal ayrıntısı yüklendi.");
    });
  }

  async function submitReview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) {
      setFeedback("Önce bir Proposal seçin.");
      return;
    }
    await execute(async () => {
      const response = await client().reviewProposal(selected.proposal_id, {
        decision,
        rationale: rationale || undefined,
        reason_code: reasonCode || undefined,
        policy_version: policyVersion || undefined,
        risk_policy_version: riskPolicyVersion || undefined
      });
      setLastReview(response);
      setSelected({
        ...selected,
        review_state: response.decision,
        review: response
      });
      if (selected.proposal_kind === "SOURCE_BRIEF") {
        setBundle((current) => ({
          ...current,
          source_brief_review_decision_id:
            response.proposal_review_decision_id
        }));
      }
      if (selected.proposal_kind === "CANDIDATE_CASE") {
        setCandidateProposalId(selected.proposal_id);
        setCandidateReviewDecisionId(response.proposal_review_decision_id);
      }
      setFeedback(`Terminal inceleme kaydedildi: ${response.decision}`);
    });
  }

  async function submitBundle(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected || selected.proposal_kind !== "SOURCE_BRIEF") {
      setFeedback("Aday paket için bir SOURCE_BRIEF seçilmelidir.");
      return;
    }
    if (selected.review_state !== "ACCEPTED") {
      setFeedback("SOURCE_BRIEF bağımsız olarak ACCEPTED olmalıdır.");
      return;
    }
    await execute(async () => {
      const response = await client().buildCandidateBundle(
        selected.proposal_id,
        bundle
      );
      setBundleResult(response);
      setCandidateProposalId(response.candidate_case_proposal_id);
      setCandidateReviewDecisionId("");
      setIdempotencyKey("");
      setFeedback(
        "Aday paket oluşturuldu. Üç Proposal bağımsız inceleme için PENDING durumunda."
      );
    });
  }

  function deriveProjectionKey() {
    try {
      setIdempotencyKey(
        projectionIdempotencyKey(
          candidateProposalId,
          candidateReviewDecisionId
        )
      );
      setFeedback("Lineage’a sabit projeksiyon anahtarı oluşturuldu.");
    } catch (error) {
      setFeedback(messageFor(error));
    }
  }

  async function submitProjection(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!candidateProposalId || !candidateReviewDecisionId || !idempotencyKey) {
      setFeedback(
        "Candidate Proposal, ACCEPTED review kararı ve idempotency anahtarı gereklidir."
      );
      return;
    }
    await execute(async () => {
      const response = await client().projectCandidate(candidateProposalId, {
        proposal_review_decision_id: candidateReviewDecisionId,
        profile_code: profileCode,
        profile_version: profileVersion,
        idempotency_key: idempotencyKey
      });
      setProjectionResult(response);
      setFeedback(
        `Projeksiyon tamamlandı: Content Authoring ${response.lifecycle_state}`
      );
    });
  }

  return (
    <main className="appShell">
      <header className="hero">
        <div>
          <p className="eyebrow">KEFE · Admin Studio</p>
          <h1>Editoryal operasyon çalışma alanı</h1>
          <p className="heroCopy">
            İnceleme, aday paket ve DRAFT projeksiyonu birbirinden ayrı insan
            komutlarıdır. Bu ekran hiçbir eylemi otomatik çalıştırmaz.
          </p>
        </div>
        <div className="securityCard" aria-label="Güvenlik durumu">
          <strong>Commit / review boundaries aktif</strong>
          <span>Cookie session · explicit CSRF · API authority</span>
        </div>
      </header>

      <section className="connectionPanel" aria-labelledby="connection-title">
        <div>
          <h2 id="connection-title">Bağlantı ve oturum</h2>
          <p>
            CSRF değeri yalnızca bu sekmenin belleğinde tutulur; kalıcı depolamaya
            yazılmaz.
          </p>
        </div>
        <label>
          Admin API adresi
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
            placeholder="Yazma işlemleri için gerekli"
            type="password"
            value={csrfToken}
          />
        </label>
        <button disabled={busy} onClick={verifySession} type="button">
          Oturumu doğrula
        </button>
        {session ? (
          <p className="sessionSummary">
            Oturum: {session.session_id} · Roller: {session.roles.join(", ") || "—"}
          </p>
        ) : null}
      </section>

      <WorkspaceStepper active={stage} onSelect={setStage} />

      <div aria-live="polite" className="feedback" role="status">
        {busy ? "İşlem sürüyor…" : feedback}
      </div>

      {stage === "QUEUE" ? (
        <section className="workspaceCard" aria-labelledby="queue-title">
          <div className="sectionHeading">
            <div>
              <p className="eyebrow">1 · Queue</p>
              <h2 id="queue-title">Proposal iş listesi</h2>
            </div>
            <button disabled={busy} onClick={() => loadQueue()} type="button">
              Listeyi yükle
            </button>
          </div>
          <div className="filterGrid">
            <label>
              İnceleme durumu
              <select
                onChange={(event) =>
                  setReviewState(event.target.value as ProposalReviewState | "")
                }
                value={reviewState}
              >
                <option value="">Tümü</option>
                <option value="PENDING">PENDING</option>
                <option value="ACCEPTED">ACCEPTED</option>
                <option value="REJECTED">REJECTED</option>
                <option value="CHANGES_REQUESTED">CHANGES_REQUESTED</option>
              </select>
            </label>
            <label>
              Proposal türü
              <input
                onChange={(event) => setProposalKind(event.target.value)}
                placeholder="SOURCE_BRIEF"
                value={proposalKind}
              />
            </label>
            <label>
              Risk kodu
              <input
                onChange={(event) => setRiskCode(event.target.value)}
                value={riskCode}
              />
            </label>
            <label>
              Pipeline
              <input
                onChange={(event) => setPipelineCode(event.target.value)}
                value={pipelineCode}
              />
            </label>
          </div>
          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>Tür</th>
                  <th>Durum</th>
                  <th>Risk</th>
                  <th>Oluşturma</th>
                  <th>İşlem</th>
                </tr>
              </thead>
              <tbody>
                {queue.map((item) => (
                  <tr key={item.proposal_id}>
                    <td>
                      <strong>{item.proposal_kind}</strong>
                      <small>{item.proposal_id}</small>
                    </td>
                    <td>
                      <StatusBadge state={item.review_state} />
                    </td>
                    <td>{item.risk_code ?? "—"}</td>
                    <td>{new Date(item.created_at).toLocaleString("tr-TR")}</td>
                    <td>
                      <button
                        disabled={busy}
                        onClick={() => selectProposal(item.proposal_id)}
                        type="button"
                      >
                        Aç
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {nextCursor ? (
            <button disabled={busy} onClick={() => loadQueue(nextCursor)} type="button">
              Sonraki sayfa
            </button>
          ) : null}
        </section>
      ) : null}

      {stage === "REVIEW" ? (
        <section className="workspaceCard" aria-labelledby="review-title">
          <div className="sectionHeading">
            <div>
              <p className="eyebrow">2 · Review</p>
              <h2 id="review-title">Bağımsız Proposal incelemesi</h2>
            </div>
            {selected ? <StatusBadge state={selected.review_state} /> : null}
          </div>
          {!selected ? (
            <p>İş listesinden bir Proposal seçin.</p>
          ) : (
            <>
              <Metadata proposal={selected} />
              <details>
                <summary>Bounded payload</summary>
                <pre>{JSON.stringify(selected.payload, null, 2)}</pre>
              </details>
              {selected.review_state === "PENDING" ? (
                <form className="stackForm" onSubmit={submitReview}>
                  <label>
                    Terminal karar
                    <select
                      onChange={(event) =>
                        setDecision(event.target.value as ProposalReviewDecision)
                      }
                      value={decision}
                    >
                      <option value="ACCEPTED">ACCEPTED</option>
                      <option value="CHANGES_REQUESTED">CHANGES_REQUESTED</option>
                      <option value="REJECTED">REJECTED</option>
                    </select>
                  </label>
                  <label>
                    Gerekçe
                    <textarea
                      maxLength={5000}
                      onChange={(event) => setRationale(event.target.value)}
                      rows={4}
                      value={rationale}
                    />
                  </label>
                  <div className="filterGrid">
                    <label>
                      Reason code
                      <input
                        onChange={(event) => setReasonCode(event.target.value)}
                        value={reasonCode}
                      />
                    </label>
                    <label>
                      Policy version
                      <input
                        onChange={(event) => setPolicyVersion(event.target.value)}
                        value={policyVersion}
                      />
                    </label>
                    <label>
                      Risk policy version
                      <input
                        onChange={(event) => setRiskPolicyVersion(event.target.value)}
                        value={riskPolicyVersion}
                      />
                    </label>
                  </div>
                  <button disabled={busy} type="submit">
                    Terminal kararı kaydet
                  </button>
                </form>
              ) : (
                <p>
                  Bu Proposal için terminal karar zaten mevcut. Yeni bir karar
                  otomatik veya tekrar oluşturulamaz.
                </p>
              )}
              {lastReview ? (
                <p className="successPanel">
                  Review decision: {lastReview.proposal_review_decision_id}
                </p>
              ) : null}
            </>
          )}
        </section>
      ) : null}

      {stage === "BUNDLE" ? (
        <section className="workspaceCard" aria-labelledby="bundle-title">
          <div className="sectionHeading">
            <div>
              <p className="eyebrow">3 · Candidate Bundle</p>
              <h2 id="bundle-title">SOURCE_BRIEF → review-required aday paket</h2>
            </div>
          </div>
          <p>
            Yalnızca terminal <strong>ACCEPTED SOURCE_BRIEF</strong> seçiliyken
            çalışır. Metin ve yapı tercihleri editör tarafından açıkça girilir.
          </p>
          <form className="stackForm" onSubmit={submitBundle}>
            <div className="filterGrid">
              <label>
                Source Brief review decision
                <input
                  onChange={(event) =>
                    setBundle({
                      ...bundle,
                      source_brief_review_decision_id: event.target.value
                    })
                  }
                  required
                  value={bundle.source_brief_review_decision_id}
                />
              </label>
              <label>
                Slug
                <input
                  onChange={(event) =>
                    setBundle({ ...bundle, slug: event.target.value })
                  }
                  pattern="[a-z0-9]+(?:-[a-z0-9]+)*"
                  required
                  value={bundle.slug}
                />
              </label>
              <label>
                Locale
                <input
                  onChange={(event) =>
                    setBundle({ ...bundle, content_locale: event.target.value })
                  }
                  required
                  value={bundle.content_locale}
                />
              </label>
              <label>
                Market scope
                <select
                  onChange={(event) =>
                    setBundle({ ...bundle, market_scope: event.target.value })
                  }
                  value={bundle.market_scope}
                >
                  <option value="GLOBAL">GLOBAL</option>
                  <option value="COUNTRY_SET">COUNTRY_SET</option>
                </select>
              </label>
            </div>
            <label>
              Başlık
              <input
                onChange={(event) =>
                  setBundle({ ...bundle, title: event.target.value })
                }
                required
                value={bundle.title}
              />
            </label>
            <label>
              Özet
              <textarea
                onChange={(event) =>
                  setBundle({ ...bundle, summary: event.target.value })
                }
                required
                rows={4}
                value={bundle.summary}
              />
            </label>
            <div className="filterGrid">
              <label>
                Base format
                <input
                  onChange={(event) =>
                    setBundle({ ...bundle, base_format_code: event.target.value })
                  }
                  required
                  value={bundle.base_format_code}
                />
              </label>
              <label>
                Primary domain
                <input
                  onChange={(event) =>
                    setBundle({
                      ...bundle,
                      primary_domain_code: event.target.value
                    })
                  }
                  required
                  value={bundle.primary_domain_code}
                />
              </label>
              <label>
                Content risk
                <input
                  onChange={(event) =>
                    setBundle({ ...bundle, content_risk: event.target.value })
                  }
                  required
                  value={bundle.content_risk}
                />
              </label>
              <label>
                Flow template
                <input
                  onChange={(event) =>
                    setBundle({ ...bundle, flow_template_code: event.target.value })
                  }
                  required
                  value={bundle.flow_template_code}
                />
              </label>
              <label>
                Flow version
                <input
                  min={1}
                  onChange={(event) =>
                    setBundle({
                      ...bundle,
                      flow_template_version_no: Number(event.target.value)
                    })
                  }
                  type="number"
                  value={bundle.flow_template_version_no}
                />
              </label>
            </div>
            <div className="filterGrid">
              <label>
                Issue code
                <input
                  onChange={(event) =>
                    setBundle({ ...bundle, issue_code: event.target.value })
                  }
                  required
                  value={bundle.issue_code}
                />
              </label>
              <label>
                Issue title
                <input
                  onChange={(event) =>
                    setBundle({ ...bundle, issue_title: event.target.value })
                  }
                  required
                  value={bundle.issue_title}
                />
              </label>
              <label>
                Question stable code
                <input
                  onChange={(event) =>
                    setBundle({
                      ...bundle,
                      question_stable_code: event.target.value
                    })
                  }
                  required
                  value={bundle.question_stable_code}
                />
              </label>
            </div>
            <label>
              Soru
              <textarea
                onChange={(event) =>
                  setBundle({ ...bundle, question_prompt: event.target.value })
                }
                required
                rows={3}
                value={bundle.question_prompt}
              />
            </label>
            <div className="filterGrid">
              <label>
                Yanıt seçenekleri (satır/virgül)
                <textarea
                  onChange={(event) =>
                    setBundle({
                      ...bundle,
                      response_options: splitList(event.target.value)
                    })
                  }
                  required
                  rows={3}
                  value={bundle.response_options.join("\n")}
                />
              </label>
              <label>
                Ülke kodları
                <textarea
                  onChange={(event) =>
                    setBundle({
                      ...bundle,
                      country_codes: splitList(event.target.value)
                    })
                  }
                  rows={3}
                  value={bundle.country_codes.join("\n")}
                />
              </label>
              <label>
                Zorunlu review mode'ları
                <textarea
                  onChange={(event) =>
                    setBundle({
                      ...bundle,
                      required_review_modes: splitList(event.target.value)
                    })
                  }
                  required
                  rows={3}
                  value={bundle.required_review_modes.join("\n")}
                />
              </label>
            </div>
            <label>
              Context title
              <input
                onChange={(event) =>
                  setBundle({ ...bundle, context_title: event.target.value })
                }
                required
                value={bundle.context_title}
              />
            </label>
            <div className="checkRow">
              <label>
                <input
                  checked={bundle.is_fact_bearing}
                  onChange={(event) =>
                    setBundle({ ...bundle, is_fact_bearing: event.target.checked })
                  }
                  type="checkbox"
                />
                Fact-bearing
              </label>
              <label>
                <input
                  checked={bundle.is_real_event}
                  onChange={(event) =>
                    setBundle({ ...bundle, is_real_event: event.target.checked })
                  }
                  type="checkbox"
                />
                Real event
              </label>
            </div>
            <button disabled={busy} type="submit">
              Aday paketi açık komutla oluştur
            </button>
          </form>
          {bundleResult ? (
            <div className="resultPanel">
              <h3>Üç bağımsız PENDING Proposal</h3>
              <p>DECISION_PROBLEM: {bundleResult.decision_problem_proposal_id}</p>
              <p>QUESTION_DRAFT: {bundleResult.question_draft_proposal_id}</p>
              <p>CANDIDATE_CASE: {bundleResult.candidate_case_proposal_id}</p>
              <button onClick={() => setStage("REVIEW")} type="button">
                İş listesine dönüp ayrı ayrı incele
              </button>
            </div>
          ) : null}
        </section>
      ) : null}

      {stage === "PROJECTION" ? (
        <section className="workspaceCard" aria-labelledby="projection-title">
          <div className="sectionHeading">
            <div>
              <p className="eyebrow">4 · Explicit Projection</p>
              <h2 id="projection-title">ACCEPTED Candidate Case → DRAFT</h2>
            </div>
          </div>
          <p>
            Bu komut yalnız Content Authoring <strong>DRAFT</strong> oluşturur veya
            aynı projeksiyonu tekrar döndürür. Submit, approve ve publish etmez.
          </p>
          <form className="stackForm" onSubmit={submitProjection}>
            <label>
              Candidate Case Proposal
              <input
                onChange={(event) => {
                  setCandidateProposalId(event.target.value);
                  setIdempotencyKey("");
                }}
                required
                value={candidateProposalId}
              />
            </label>
            <label>
              Candidate Case ACCEPTED review decision
              <input
                onChange={(event) => {
                  setCandidateReviewDecisionId(event.target.value);
                  setIdempotencyKey("");
                }}
                required
                value={candidateReviewDecisionId}
              />
            </label>
            <div className="filterGrid">
              <label>
                Projection profile
                <input
                  onChange={(event) => setProfileCode(event.target.value)}
                  required
                  value={profileCode}
                />
              </label>
              <label>
                Profile version
                <input
                  min={1}
                  onChange={(event) => setProfileVersion(Number(event.target.value))}
                  type="number"
                  value={profileVersion}
                />
              </label>
            </div>
            <div className="inlineAction">
              <label>
                İdempotency key
                <input
                  maxLength={200}
                  onChange={(event) => setIdempotencyKey(event.target.value)}
                  required
                  value={idempotencyKey}
                />
              </label>
              <button onClick={deriveProjectionKey} type="button">
                Lineage’dan üret
              </button>
            </div>
            <button disabled={busy} type="submit">
              DRAFT projeksiyonunu açıkça çalıştır
            </button>
          </form>
          {projectionResult ? (
            <div className="resultPanel">
              <h3>Content Authoring {projectionResult.lifecycle_state}</h3>
              <p>Case: {projectionResult.authoring_case_id}</p>
              <p>CaseVersion: {projectionResult.authoring_case_version_id}</p>
              <p>Projection: {projectionResult.projection_record_id}</p>
              <p>Replay: {projectionResult.replayed ? "Evet" : "Hayır"}</p>
              <strong>Bu ekranda yayınlama yetkisi yoktur.</strong>
            </div>
          ) : null}
        </section>
      ) : null}
    </main>
  );
}
