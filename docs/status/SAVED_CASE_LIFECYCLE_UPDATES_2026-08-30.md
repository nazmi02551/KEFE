# Saved Case lifecycle updates — 2026-08-30

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #389  
Pull request: #390  
Capability: CAP-079 (`IMPLEMENTED_PARTIAL`)  
Stack base: PR #388 exact-green head
`9e4f5bcf24fd75dd0897529d5c5ea66486f08ae2`

ADR: ADR-0139  
Contract: `docs/contracts/saved-case-lifecycle-updates.v1.json`

## User-visible outcome

Activity compares a device-local saved Case snapshot with the successfully
fetched canonical Explore collection. When the exact Case id matches but the
published CaseVersion id differs, the Saved Cases surface shows a localized
update count and per-Case update marker. Opening the current Case acknowledges
the observed version while preserving the original save timestamp.

This closes the silent-staleness gap for foreground Activity use without
pretending that KEFE already has a push-notification or account-sync platform.

## Truthful state boundary

- only exact Case and CaseVersion identity participate in comparison;
- catalog loading, failure and absence produce no update or removal claim;
- saved entries remain available when catalog refresh fails;
- acknowledgement refreshes only the existing presentation snapshot;
- the `kefe.saved_cases.v1` payload, storage key and backward compatibility are
  unchanged;
- Activity pull-to-refresh covers progress, saved snapshots and the current
  foreground catalog.

## Product and privacy boundary

The implementation is shared by Production and Product Preview, supports
Turkish/English, light/dark themes, compact phones, enlarged text and semantic
update disclosure. It preserves Activity as the saved-Case continuity owner and
continues through `/case/:caseId`.

No actor identity, response, private reason, notification history, targeting,
recommendation or inferred trait is stored. Server synchronization, account
migration, cross-device restore, background polling, push/email delivery,
notification inbox, ranking and social graph remain separate follow-up work.

## Candidate verification

The first published runtime candidate `a988476c1f9108addf90d370850138691e11d6b4`
passed API CI, Flutter analyze and the full mobile regression suite, but its MVP
format gate correctly rejected canonical Dart drift. The workflow-produced
normalized source was applied without behavior changes in follow-up candidate
`f9cb06b1e5c0e28e47868aa8608fbedb17f17bc7`.

Final exact-head API CI, Mobile CI, MVP Beta Gates and Global Readiness evidence
will be recorded in PR #390 after all four workflows complete on the same head.
An installable artifact may be retained as CI evidence, but no APK is handed off
merely because this draft candidate exists.

## Non-claims

This draft does not complete CAP-079, prove background or external notification
delivery, establish cross-device continuity, prove human usability, promote a
release or advance `docs/status/CURRENT.md`.

