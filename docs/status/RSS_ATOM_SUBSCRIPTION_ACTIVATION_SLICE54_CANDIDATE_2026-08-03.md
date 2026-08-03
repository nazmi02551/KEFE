# RSS/Atom Subscription Activation — Slice 54 Candidate

- Date: 2026-08-03
- Issue: #266
- Branch: `feature/rss-atom-subscription-activation-slice54`
- Base: `feature/feed-item-extraction-slice53` / PR #232
- Status: Candidate; exact-head CI pending

## Implemented

- Accepted ADR-0090 and executable Slice 54 contract.
- Added immutable versioned RSS/Atom subscription manifests.
- Added deterministic manifest registry with shared-adapter policy-drift rejection.
- Derived controlled HTTP adoption origins only from exact registered feed locators.
- Reused the existing evidence-backed public HTTP adapter factory and strict RSS/Atom definition.
- Reused the exact Slice 53 feed-item extraction runtime.
- Added explicit capability-first, schedule-second activation service.
- Composed an empty production manifest registry and exposed the dormant activation boundary without invoking it.
- Added manifest, assembly, activation, failure/retry and end-to-end scheduler-to-proposal tests.
- Added architecture fitness and dedicated RSS Atom Subscription Activation CI.

## Preserved boundaries

- No concrete external feed is registered.
- No subscription is activated during application startup.
- No live external network test is used.
- No provider legal/compliance, deployed egress or durable backend capability is claimed.
- No credentials, secret references or auth headers enter the public manifest.
- No automatic review, materialization, Claim/Case creation or publication is introduced.
- No Admin subscription API/UI or phone-facing feed behavior is introduced.

## Validation

Do not call this slice PASS and do not mark its PR ready until all required workflows complete successfully on one exact runtime SHA. Do not merge before the full parent stack is merged in order.
