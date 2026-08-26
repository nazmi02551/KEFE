# MVP Today Discovery — 2026-08-26

Status: Planning checkpoint

## Goal
Create a governed KEFE Today projection without inferring current events from category, domain, or presentation labels.

## Boundary
Today must only surface cases explicitly marked by trusted editorial/runtime metadata. The mobile client must not guess eligibility.

## Planned slice
- server-side Today read projection
- additive API contract
- regression tests for real-event selection and empty state
- mobile consumer integration

No implementation claims are made until exact commits and tests are recorded.
