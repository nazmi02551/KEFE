# ADR-0126 — External two-actor Connected Alpha acceptance proof

Status: Proposed / F4 candidate

Issue: #351

Parent: PR #350 / `a0989c27ad1c3f430e08ecc9ff6c0ba7a9350215`

## Context

Repository tests, container builds, Product Preview and compile-only mobile artifacts cannot prove that two independent phones or clients are using one externally reachable KEFE backend and one shared PostgreSQL state.

Once schema bootstrap and deployment exist, KEFE needs a narrow evidence procedure that proves this exact product property without becoming a load test, survey-methodology claim or store-readiness claim.

The Connected Alpha RAW Collective Result bridge makes a deterministic shared-state assertion possible: if actor 2 is drafted but uncommitted, actor 1's reveal must exclude actor 2; after actor 2 commits, the shared RAW sample size must increase by exactly one and actor 1 must reread the same aggregate.

## Decision

Adopt a provider-neutral operator tool, `services/api/tools/run_connected_alpha_acceptance.py`, as the external Connected Alpha multi-user evidence harness.

The tool must fail closed unless all of the following are explicit:

- a valid external HTTPS base URL;
- a dedicated acceptance Case UUID;
- `--allow-write`;
- a bounded timeout.

It must never select an arbitrary public Case automatically.

## Required acceptance sequence

1. Probe `/health`.
2. Probe `/ready`.
3. Fetch the explicit Case and discover a required SINGLE_CHOICE question with at least two configured options.
4. Create exactly two guest actors.
5. Create and answer both drafts with different valid choices.
6. Commit actor 1 and require RAW reveal.
7. Commit actor 2 and require `n2 = n1 + 1`.
8. Reread actor 1 and require the same shared `n` and option payload as actor 2.
9. Delete both actors through the existing actor-bound privacy self-service endpoint.
10. Treat cleanup failure as acceptance failure.

## Why a dedicated Case is required

The proof creates two real committed decisions before deleting the actors. An operator-selected dedicated acceptance Case prevents accidental writes to a live editorial Case and prevents a pre-existing TRUSTED snapshot from being mistaken for live RAW evidence.

If reveal returns TRUSTED, the tool fails and asks for a dedicated no-TRUSTED acceptance Case rather than weakening the assertion.

## Privacy boundary

The harness does not send:

- private reason text/tags;
- confidence answers;
- demographics;
- profile data.

It stores no bearer token or actor ID in the acceptance record. Cleanup uses the canonical `DELETE /v1/me` actor-bound confirmation and runs in `finally` for every actor created during the attempt.

## Evidence record

On success, the tool may emit only a redacted `connected-alpha-acceptance.v1` JSON record containing deployment origin, Case/CaseVersion identifiers, RAW layer, sample sizes before/after the second commit, actor count, exact source commit, timestamps and cleanup status.

This record is not automatically committed and does not automatically promote reachability or capability lifecycle state. Human/operator review remains required.

## CI boundary

Repository CI validates the harness with fake transport only. CI must not receive a production/alpha endpoint secret and must not perform external writes automatically.

A real run is a separately initiated operator action only after deployment identity and dedicated acceptance content exist.

## Non-claims

A successful run proves the observed external two-actor shared-state path at one point in time. It does not prove representativeness, Signal, Impact, load capacity, SLO attainment, broad availability, store readiness, F4 completion or CAP-123 lifecycle promotion.
