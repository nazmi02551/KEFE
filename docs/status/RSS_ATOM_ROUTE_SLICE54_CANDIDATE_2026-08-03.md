# RSS/Atom Route Slice 54 Candidate — 2026-08-03

## Candidate scope

Slice 54 assembles the existing PUBLIC provider, controlled HTTP, immutable evidence, SourceAcquisition and feed-item extraction primitives into one immutable provider-neutral route bundle.

The route profile pins:

- one versioned route code;
- one versioned adapter code;
- one exact `StrictRssAtomParseProfile`;
- optional locale and jurisdiction context;
- the exact `RSS_ATOM_FEED_ITEM_EXTRACTION` v1.0.0 pipeline;
- a deterministic canonical SHA-256 configuration hash.

The route factory uses the same parser-profile object for feed-snapshot capture and feed-item extraction, and the same evidence-store object for sealing and integrity-verified reading.

## Production boundary

Production composition constructs the route factory and an empty `InMemoryRssAtomRouteRegistry`. It registers:

- zero route profiles or bundles;
- zero concrete RSS/Atom public adapters;
- zero feed-item ingestion worker plans;
- zero concrete providers or feed URLs.

No live capture, schedule, review, materialization, projection, Case creation or publication is enabled.

## Candidate validation

Pending exact-head CI. Required evidence:

- RSS Atom Route CI;
- parent provider/evidence/RSS/extraction/ingestion architecture gates;
- full PUBLIC permit-to-FEED_ITEM proposal vertical test;
- API CI;
- MVP Beta Gates;
- Global Readiness.

Do not call PASS or mark ready until every required workflow is green on one exact runtime SHA. Do not merge before the active parent stack.