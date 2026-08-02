# Provider HTTP Transport — Slice 45 candidate

**Issue:** #215  
**Parent:** PR #214 / Slice 44  
**Status:** CANDIDATE — exact-head CI pending

## Candidate scope

- immutable exact provider adoption profiles;
- exact HTTPS origins and GET/HEAD methods;
- explicit media, timeout, response-byte and redirect budgets;
- opaque terms/rate-limit evidence references without compliance claims;
- exact immutable adoption registry;
- URL/userinfo/port/fragment/credential-query rejection;
- resolver port with all-answers-public SSRF policy;
- deterministic public IP selection and backend pinning;
- one-hop backend with service-owned redirect revalidation;
- bounded status/media/body/timeout failures;
- privacy-safe operational allowlist;
- empty registry plus unconfigured DNS/backend in production composition;
- architecture fitness and dedicated CI.

## Explicitly not claimed

No real provider adapter, live external network, system DNS, TLS/socket backend, provider terms compliance, credential rotation, scraping/browser automation, autonomous retry, Admin UI, deployed SLO/alert/rollback evidence or phone behavior.

## Required evidence before PASS

- API CI;
- Provider Admission CI regression;
- Provider Secret Execution CI regression;
- Provider HTTP Transport CI;
- MVP Beta Gates;
- Global Readiness;
- all on the same exact runtime SHA.
