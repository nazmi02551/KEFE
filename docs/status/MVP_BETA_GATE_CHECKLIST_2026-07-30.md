# KEFE MVP Beta Gate Checklist — 2026-07-30

Authority: ADR-0036 / Issue #93

Legend:
- `AUTO` repository/CI-owned proof.
- `EXT` requires human, provider, store, editorial or deployed-environment evidence.

Repository-owned evidence checkpoint: `docs/status/MVP_CODE_COMPLETE_2026-07-30.md`
Verified code candidate: `9025f0e4d75816e46c304883c414856bff1bd7a4`

## MVP code completion

- [x] AUTO — Golden Path regression: Explore → Case → Weigh → Commit → Reveal → Perspective → My KEFE → Share.
- [x] AUTO — Guest-first onboarding remains non-blocking.
- [x] AUTO — OTP request/verify/explicit guest→account conversion and history merge.
- [x] AUTO — Share is Commit-gated, CASE-ONLY, opaque, expiring/revocable; sender decision/confidence/private reason excluded.
- [x] AUTO — Community Reason is explicit, bounded, moderated and actor-owned-COMMITTED-session gated; private Reason never auto-published.
- [x] AUTO — Privacy export/delete/retention contract and persistence tests.
- [x] AUTO — Encrypted local uncommitted drafts expire after seven days.
- [x] AUTO — uncertain Commit keeps server-authoritative same-key recovery.
- [x] AUTO — >=20 L0 DILEMMA and >=4 L0 CALL engineering catalog readiness.
- [x] AUTO — no Case-format-specific runtime Screen/Controller/Service classes.
- [x] AUTO — API/OpenAPI/error/manifest contract gates.
- [x] AUTO — PostgreSQL migration/seed/integration/outbox gates.
- [x] AUTO — Flutter format/analyze/widget/accessibility/locale/theme gates.
- [x] AUTO — repeatable critical-path in-process performance budget harness.
- [x] AUTO — operations rollback/kill-switch runbook exists.
- [x] AUTO — exact candidate SHA and artifacts recorded in CURRENT/status checkpoint.

All AUTO items are green on one exact code candidate. Repository status is therefore:

`MVP_CODE_COMPLETE / BETA_GATE_PENDING`

Evidence:
- MVP Beta Gates run `30516434466` — SUCCESS
- API CI run `30516434447` — SUCCESS
- Mobile CI run `30516434450` — SUCCESS
- exact code SHA `9025f0e4d75816e46c304883c414856bff1bd7a4`

## External beta gate

- [ ] EXT — real production OTP delivery provider configured and deliverability verified.
- [ ] EXT — human phone usability checklist passes on candidate APK/build.
- [ ] EXT — editorial CQB accepts the launch content pool.
- [ ] EXT — current Apple/Google store compliance review passes at release time.
- [ ] EXT — deployed environment verifies production SLO/load/observability targets.
- [ ] EXT — concrete production feature-flag/rollback controls validated by operator.

Only after these are evidenced may the product be called `BETA_GATE_PASSED` or public/store release-ready.
