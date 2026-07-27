# ADR-0007 — Private-by-default structured reason capture

**Status:** Accepted  
**Date:** 2026-07-27

## Context

KEFE must capture why a user made a decision without turning the first MVP into an unmoderated social-comment feed. Reason data can contain sensitive opinions, personal information, harassment or defamatory claims. It must also remain tied to the exact WeighSession and pinned CaseVersion that produced the decision.

## Decision

- Reason capture is a separate Decision capability, not an ordinary public comment object.
- A reason is optional for M0 and can contain:
  - zero or more Case-configured structured tags;
  - optional short text when the Case schema explicitly enables it.
- Allowed tags, maximum tag count and short-text limit are defined in the published question schema. They are not hard-coded by the client.
- Reason records are stored one-per-WeighSession in `decision.private_reason`.
- Visibility is fixed to `PRIVATE` in this slice. No consumer endpoint exposes another user's reason.
- Tags-only reasons use moderation state `NOT_REQUIRED`.
- Any reason containing free text enters moderation state `PENDING`.
- The reason can be changed only while the WeighSession is `DRAFT`; it becomes immutable at Commit together with the decision.
- Repository updates lock the owning WeighSession row so a competing Commit cannot race a stale reason edit.
- Public reason ranking, persuasion metrics, AI clustering and community visibility are explicitly deferred until moderation and methodology contracts are implemented.

## Consequences

- KEFE can collect structured rationale for future personal insight and research without creating a public social surface.
- Free text is retained behind a moderation state and private visibility boundary.
- A later moderation worker can transition `PENDING` to `ALLOWED` or `BLOCKED` without changing the decision itself.
- A later Perspective layer may consume only policy-eligible, aggregated or moderated reasons.
- Client applications must treat the server-provided reason schema as authoritative.
