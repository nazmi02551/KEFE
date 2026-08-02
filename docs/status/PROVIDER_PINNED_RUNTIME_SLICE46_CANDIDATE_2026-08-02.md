# Provider Pinned Runtime — Slice 46 Candidate

**Date:** 2026-08-02  
**Issue:** #217  
**Parent:** PR #216 / Slice 45  
**Status:** CANDIDATE — exact-head CI pending

## Candidate boundary

This slice adds an explicitly activated provider-neutral DNS/TLS runtime behind ADR-0081:

- exact `DISABLED | PINNED_TLS` mode with `DISABLED` default;
- bounded system DNS candidate collection without authorization filtering;
- exact selected-IP TCP connection;
- approved host used for TLS SNI and certificate verification;
- TLS 1.2 minimum, required certificate/hostname verification and no insecure fallback;
- one GET/HEAD HTTP/1.1 request with no body, proxy, cookies, redirect following or ambient credentials;
- bounded projected response headers, content framing and body reads;
- bounded retryable/final error mapping;
- empty provider-adoption registry in every runtime mode.

## Evidence required before PASS

- Provider Pinned Runtime CI exact-head PASS;
- Provider HTTP Transport CI parent regression PASS;
- Provider Secret Execution CI PASS;
- Provider Admission CI PASS;
- API CI including PostgreSQL PASS;
- MVP Beta Gates PASS;
- Global Readiness PASS.

## Explicit non-claims

This candidate does not prove or enable a real provider adoption, live external provider success, deployed firewall/VPC/NAT policy, secret header injection, provider legal compliance, production SLOs or phone-facing provider behavior.
