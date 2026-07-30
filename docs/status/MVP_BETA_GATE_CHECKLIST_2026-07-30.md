# KEFE MVP Beta Gate Checklist — 2026-07-30

Authority: ADR-0036 / Issue #93

Legend:
- `AUTO` repository/CI-owned proof.
- `EXT` requires human, provider, store, editorial or deployed-environment evidence.

## MVP code completion

- [ ] AUTO — Golden Path regression: Explore → Case → Weigh → Commit → Reveal → Perspective → My KEFE → Share.
- [ ] AUTO — Guest-first onboarding remains non-blocking.
- [ ] AUTO — OTP request/verify/explicit guest→account conversion and history merge.
- [ ] AUTO — Share is Commit-gated, opaque, expiring/revocable; private reason excluded.
- [ ] AUTO — Community Reason is explicit, bounded, moderated; private Reason never auto-published.
- [ ] AUTO — Privacy export/delete/retention contract and persistence tests.
- [ ] AUTO — Encrypted local uncommitted drafts expire after seven days.
- [ ] AUTO — uncertain Commit keeps server-authoritative same-key recovery.
- [ ] AUTO — >=20 L0 DILEMMA and >=4 L0 CALL engineering catalog readiness.
- [ ] AUTO — no Case-format-specific runtime Screen/Controller/Service classes.
- [ ] AUTO — API/OpenAPI/error/manifest contract gates.
- [ ] AUTO — PostgreSQL migration/seed/integration/outbox gates.
- [ ] AUTO — Flutter format/analyze/widget/accessibility/locale/theme gates.
- [ ] AUTO — repeatable critical-path in-process performance budget harness.
- [ ] AUTO — operations rollback/kill-switch runbook exists.
- [ ] AUTO — exact candidate SHA and artifacts recorded in CURRENT/status checkpoint.

When every AUTO item is green on one head, repository status may become:

`MVP_CODE_COMPLETE / BETA_GATE_PENDING`

## External beta gate

- [ ] EXT — real production OTP delivery provider configured and deliverability verified.
- [ ] EXT — human phone usability checklist passes on candidate APK/build.
- [ ] EXT — editorial CQB accepts the launch content pool.
- [ ] EXT — current Apple/Google store compliance review passes at release time.
- [ ] EXT — deployed environment verifies production SLO/load/observability targets.
- [ ] EXT — concrete production feature-flag/rollback controls validated by operator.

Only after these are evidenced may the product be called `BETA_GATE_PASSED` or public/store release-ready.
