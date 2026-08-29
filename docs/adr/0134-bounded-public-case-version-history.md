# ADR-0134 — Bounded public CaseVersion history

Status: IMPLEMENTATION CANDIDATE  
Date: 2026-08-27  
Issue: #376  
Capabilities: CAP-072 (primary), CAP-026 and CAP-095 (supporting)

## Context

KEFE publishes immutable CaseVersions and atomically marks the previously public
version `SUPERSEDED` when a later version is published. The consumer journey can
currently read only the active version. A reader therefore cannot tell which
immutable versions were previously public, even though the canonical consumer
store already retains that history.

The editorial store contains substantially more information: drafts, review
states, reviewer identity, lifecycle commands and rationales. Those records are
not public history and must not leak through a consumer endpoint. A superseded
version also does not, by itself, prove that a correction occurred or explain
why a new version was published.

## Decision

Add a bounded, read-only public history projection for a Case:

1. `GET /v1/cases/{case_id}/history` is available only while the Case has an
   active `PUBLISHED` consumer CaseVersion and its Case item is published;
2. the response contains only immutable consumer versions whose exact status is
   `PUBLISHED` or `SUPERSEDED`;
3. records are ordered by `version_no DESC` and bounded to at most 20;
4. every record exposes only CaseVersion id, version number, title, summary,
   optional publication timestamp and exact `CURRENT` / `PREVIOUS` public
   classification;
5. withdrawn and non-public editorial states, actor references, audit commands,
   rationales and review records are never returned;
6. a superseded record is described as a previous published version, not as a
   correction, because the current model has no public correction record;
7. the mobile surface is read-only, localized in English and Turkish, and does
   not block Context, Weigh or Commit if history is unavailable;
8. Product Preview may project its one current fixture but must not invent a
   previous public version.

The endpoint is case-agnostic. KEFE Today receives the same trust affordance as
every other Case and no Today-specific history engine is introduced.

## Ordering and fail-closed rules

The server is the ordering authority. `version_no` is not reinterpreted by the
client. Duplicate version numbers, a missing current record, an unknown public
classification or malformed identifiers make the mobile response unavailable;
they are not silently rendered as history.

An empty repository result is `CASE_NOT_FOUND`, not an empty success. This keeps
withdrawn or never-published Case identities from becoming a public discovery
surface through the history route.

## Preserved architecture

- published CaseVersion remains immutable;
- Commit First and Blind First remain unchanged;
- the endpoint contains no collective result, Perspective, Signal or Impact;
- public history is read from the consumer projection rather than directly
  exposing the editorial aggregate or audit log;
- Product Preview and connected/production compositions remain isolated;
- raw titles and summaries are returned unchanged by the API; existing display
  localization rules continue to govern presentation.

## Consequences

This advances the public Case-version portion of CAP-072. Source correction
history, correction reasons, human editorial acceptance and a source
verification methodology remain separate future decisions. CAP-072, CAP-026
and CAP-095 receive no lifecycle promotion from this candidate.

