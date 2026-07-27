# ADR-0008 — Offline-safe mobile Reason Capture

**Status:** Accepted  
**Date:** 2026-07-27

## Context

ADR-0007 establishes private-by-default structured Reason Capture on the server. The mobile client must expose that capability without making a reason mandatory, hard-coding editorial options, weakening Commit First or losing a user's rationale when connectivity becomes uncertain.

Mobile decision drafts already pin the CaseVersion and preserve responses plus the Commit idempotency key. Reason Capture must participate in the same durable boundary because a reason belongs to the exact WeighSession that produced the decision and becomes immutable at Commit.

## Decision

- Mobile renders one optional Reason Capture card in the Case flow, after the schema-driven questions and before the semantic `COMMIT` action.
- A blank reason never blocks Commit and does not call the private reason endpoint.
- One reason is captured per WeighSession in this M0 slice, consistent with ADR-0007.
- Allowed tag identifiers, maximum tag count, short-text enablement and short-text length come from the published CaseVersion question schema.
- The client does not hard-code which tags are available. Semantic localization may map known tag identifiers to human-readable labels and must provide a safe fallback for unknown identifiers.
- The short-text input is displayed only when the schema enables it. Whitespace-only text is treated as absent.
- Reason tags and short text are persisted in the existing per-Case local draft together with the pinned CaseVersion, session ID and typed response map.
- The pre-Commit recovery state machine is:
  - `editing` — inputs can change and the local draft is updated;
  - `syncPending` — typed responses and any non-empty private reason must be synchronized;
  - `commitPending` — Commit may be attempted with the already persisted idempotency key;
  - `committedAwaitingReveal` — only Reveal may be retried.
- A user-entered reason must not be silently discarded to make Commit succeed. If response or reason synchronization has an uncertain transport outcome, the client keeps the same pinned draft, locks editing and retries pre-Commit synchronization before Commit.
- Repeating the private reason `PUT` while the WeighSession remains `DRAFT` is the recovery mechanism; no replacement WeighSession or Commit key is generated.
- Reasons remain `PRIVATE` and are not exposed in community results or the current Reveal. User-facing copy must say that the reason is not shown to other users; it must not imply that server-side safety review is impossible. Free text may enter moderation under ADR-0007.
- This slice does not decide final primary navigation, final branded Commit CTA wording, public reason visibility, Perspective ranking or AI summarization.

## Consequences

- Optional rationale can be captured without increasing the completion barrier for the core decision loop.
- The client stays compatible with editorial changes because the CaseVersion schema remains authoritative.
- Responses, rationale and Commit ordering survive restarts and uncertain connectivity as one coherent decision draft.
- Public discussion, persuasion metrics and cross-user reason surfaces remain unavailable until separate moderation and methodology decisions are accepted.
