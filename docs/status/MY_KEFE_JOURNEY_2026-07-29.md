# KEFE My KEFE Journey Checkpoint — 2026-07-29

This is a durable engineering/product checkpoint. It supplements `docs/status/CURRENT.md` and `docs/status/PRODUCT_PREVIEW_2026-07-29.md`; it does not replace the published Documentation Ecosystem v3.4 milestone.

## Architecture lock

PR #83 — `Lock descriptive My KEFE journey read model`

Added ADR-0032 and `my-kefe-journey-read-model.v1.yaml`.

Binding decisions:

- `GET /v1/me/progress` remains the actor-scoped progress endpoint and existing response members remain compatible.
- The new `journey` member is additive and summarizes only directly observed product history.
- Allowed observations include later committed decisions, revisited sessions, completed Reflections, bounded domain activity and bounded recent decision journeys.
- Historical committed Weighs remain visible when DecisionRevision or Reflection rows are absent.
- Raw response snapshots, private reasons, DecisionDelta details, Exposure and Intervention metadata are excluded.
- Personality, ideology, psychometric, bias and causal inference remain forbidden.
- Mobile continues through the shared `ProgressRepository` boundary; production may not import or fall back to preview repositories.

## Shared mobile and Product Preview runtime

PR #84 — `Make My KEFE a repository-driven decision journey`

Merge commit:

`1e2338e349fcb30f2fc1797fee58631550e503f6`

Implemented:

- typed domain-activity and recent-journey mobile models;
- backward-compatible `ProgressEnvelope` journey parsing;
- reusable `MyKefeJourneyScreen` with loading, error, empty and populated states;
- observed-only counters for committed Weighs, later decisions, revisits and Reflections;
- bounded domain activity and recent decision journeys;
- explicit non-inference and preview-data disclosure;
- deterministic `PreviewProgressRepository` injected only by the Product Preview composition;
- production entrypoint isolation from preview progress and preview media repositories;
- removal of the previous static My KEFE demo metrics.

Verified exact-head Mobile CI:

- run `30488318184` — PASS
- analyze PASS
- widget/unit tests PASS
- Android preview APK build PASS
- artifact upload PASS

Preview artifact:

- artifact name: `kefe-preview-android`
- artifact id: `8739080881`
- workflow artifact digest: `sha256:2f9b254c9d595eef0a1a28a1bdc8298353aa7c35a04d486861ade309a72f125d`
- extracted APK sha256: `75e7ad87078d7c7c7474cae2bac492b4f2f21ca85513ea26898486e9363c6666`

## Production journey API

PR #85 — `Add descriptive My KEFE journey API`

Merge commit:

`5768516574138de5bd42bda2a4bcf6ddd72f2448`

Implemented:

- additive `journey` member on `GET /v1/me/progress`;
- `decision_update_count`, `revisited_case_count`, `reflection_completion_count`, `domain_activity` and `recent_journeys`;
- memory aggregation using existing committed Weigh and optional lineage capabilities;
- PostgreSQL aggregation from committed Weighs plus optional DecisionRevision and Reflection rows;
- historical compatibility without schema migration or backfill;
- explicit methodology declaring observed product history only and no causal claims;
- exact generated OpenAPI 0.17.0 synchronization;
- contract fitness checks for the new journey schemas and fields;
- privacy tests proving response, reason and lineage payloads are not exposed.

Verified exact-head API CI:

- run `30492855919` — PASS
- lint PASS
- contract synchronization PASS
- architecture/contract gates PASS
- unit tests PASS
- OpenAPI drift gate PASS
- PostgreSQL migration, seed and integration tests PASS

## What is now real

My KEFE is no longer a static Product Preview profile mock. The same repository contract now supports:

- deterministic preview journey data for phone-based product evaluation;
- backward-compatible production HTTP parsing;
- actor-scoped production aggregation from committed decision history;
- optional DecisionRevision and Reflection enrichment;
- safe rendering when only legacy Weigh history exists.

The feature describes what the user did inside KEFE. It does not claim what kind of person the user is, what ideology they hold, why they changed a decision, or whether any viewed material caused that change.

## Remaining limitations

- Product Preview data remains deterministic example data.
- Production My KEFE requires the authenticated API/runtime environment to display real actor history.
- Cross-user comparison, similarity, recommendations and targeting remain deferred.
- Account enrollment and guest-to-account conversion remain deferred.
- Remote production media infrastructure remains deferred.
- Release signing, AAB and Play Store distribution remain deferred.

## Next boundary

The next product decision should be based on phone feedback from the now-visible end-to-end preview rather than another long invisible backend sequence. The highest-value candidates are:

1. refine My KEFE information hierarchy and journey-card language from real phone feedback;
2. connect authenticated production mobile progress to the now-available OpenAPI 0.17 journey response;
3. define the next architecture lock only after identifying the most important usability or production-read gap;
4. keep contract-manifest reconciliation as a deliberate repository-governance task rather than silently rewriting historical lineage.

## Documentation note

The published Documentation Ecosystem v3.4 remains the current packaged DOCX/PDF milestone. No package regeneration is warranted for this implementation checkpoint.
