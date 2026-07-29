# ADR-0031 — Case Media Presentation Boundary

- Status: Accepted
- Date: 2026-07-29
- Depends on: ADR-0011, ADR-0013, ADR-0022, ADR-0024, ADR-0030

## Context

The Product Preview now has a coherent shell, premium Case hierarchy, signature Weigh/Reveal treatment and a visible DecisionRevision/Reflection journey. The remaining visual gap is that Cases are still largely text-and-icon surfaces.

KEFE needs visual/media presentation metadata that can later be backed by editorial uploads, object storage/CDN renditions or other delivery infrastructure without pushing provider URLs, SDKs or media-specific assumptions into the Case, Flow, Claim or decision domains.

Media is also capable of biasing a decision. A dramatic image, misleading crop or post-result comparison visual must not silently bypass Commit-first and source/evidence rules.

## Decision

### 1. Presentation media is a separate bounded read concern

Case media presentation is not part of decision truth, Claim truth, Source evidence, Flow semantics or collective results.

Consumer UI reads media through a dedicated provider-neutral `CaseMediaRepository` boundary keyed by immutable `CaseVersion` identity.

The Case/Flow domain does not import CDN, image-host, object-storage or vendor SDK types.

### 2. Semantic media identity is immutable and CaseVersion-pinned

An approved media presentation item has a stable semantic identity and is associated with one immutable CaseVersion.

Semantic fields include:

- presentation slot;
- media kind;
- asset identity/content hash reference;
- alt text or explicit decorative state;
- caption when present;
- attribution/provenance metadata when externally sourced;
- exposure phase;
- editorial review state.

Changing the subject, crop meaning, caption, attribution, exposure phase or other semantically meaningful presentation metadata for a published Case requires a new approved CaseVersion/presentation revision according to publication governance. Delivery-only rendition changes do not create new Case semantics.

### 3. Delivery renditions are replaceable infrastructure

A semantic media item may resolve to multiple delivery renditions such as phone-card, hero or high-density variants.

Rendition locators are delivery concerns. They may later resolve through API/object storage/CDN adapters and may change for encoding, resizing, caching or host migration while retaining the same approved semantic asset identity.

Consumer presentation asks the repository for a suitable rendition; it does not construct provider URLs.

### 4. Slots and kinds are generic, not Case-type branches

Initial presentation slots:

- `EXPLORE_CARD`
- `CASE_HERO`
- `CONTEXT_SUPPORTING`

Initial media kinds:

- `IMAGE`
- `ILLUSTRATION`
- `VIDEO_POSTER`

The taxonomy is versionable/extensible. Flutter must not branch on `DILEMMA`, `SPORTS_CALL`, Domain or a named Case to choose layout semantics.

### 5. Exposure phase is explicit and Commit authority remains binding

Every informative media item declares one exposure phase:

- `PRE_COMMIT_SAFE`
- `POST_COMMIT_ONLY`

`POST_COMMIT_ONLY` media must never be rendered before the Flow runtime says the relevant post-Commit capability is available.

Preview implementations may initially expose only `PRE_COMMIT_SAFE` Case/Explore media.

Media metadata cannot open Reveal, Perspectives or another blocked Flow step.

### 6. Media does not masquerade as evidence

Presentation media may visually contextualize a Case but does not become a `CaseContextSource`, Claim evidence or fact-check input by being displayed.

Where an image itself is evidence, it must separately participate in the source/claim/evidence architecture and may also have a presentation projection. Presentation metadata alone never upgrades evidentiary status.

### 7. Accessibility is mandatory

Informative visual media requires meaningful alt text. Pure decoration must be explicitly marked decorative and excluded from redundant screen-reader narration.

UI must retain a usable text hierarchy when media is unavailable, rejected, loading or unsupported.

### 8. Media failure must not break the decision core

Media is enhancement, not a prerequisite for reading a Case, answering a typed question, committing a decision or completing Reflection.

Repository/network/media decode failures degrade to the text-first Case experience. They must not trigger preview fallback, alter decision state or fabricate media.

### 9. Preview media remains explicit deterministic preview data

`main_preview.dart` may compose a deterministic preview media repository.

Production `main.dart` may not import preview media repositories and may not activate preview media after remote failures.

Preview media must be replaceable without changing screen hierarchy or decision contracts.

### 10. Security, provenance and rights remain visible concerns

Remote implementation must validate supported schemes/content types, avoid arbitrary executable content, and use configured delivery origins rather than untrusted URL construction.

Externally sourced informative media must preserve available attribution/licensing/provenance metadata for editorial/admin review. The consumer may render attribution when required by policy.

## First implementation slice

The first permitted slice is mobile/preview focused:

1. provider-neutral media presentation domain/read models;
2. `CaseMediaRepository` interface;
3. deterministic Preview repository with no remote provider calls;
4. generic reusable media surface for Explore cards and Case hero;
5. graceful media-absent fallback;
6. exposure-phase filtering with no post-Commit media in the initial preview slice;
7. accessibility semantics;
8. tests proving production composition does not import preview media repositories and Case/Flow behavior is unchanged.

No server HTTP endpoint, object-storage adapter, CDN integration, upload workflow or Admin media workbench is authorized by this slice.

## Deferred

- production media persistence and publication workflow;
- object storage/CDN provider adapters;
- image/video processing workers;
- signed/private delivery URLs;
- Admin upload/crop/license UI;
- semantic computer-vision analysis;
- automated media generation or selection;
- video playback.

## Consequences

- KEFE can become visually richer without contaminating the decision/knowledge domains.
- Preview visuals can be replaced by production assets behind the same repository boundary.
- Commit-first integrity applies to potentially biasing media as well as textual result surfaces.
- Media failures remain non-fatal to the core decision journey.
