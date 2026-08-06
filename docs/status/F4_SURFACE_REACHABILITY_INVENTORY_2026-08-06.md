# F4 Surface Reachability Inventory — 2026-08-06

## Scope

- Foundation wave: F4
- Capabilities: CAP-092, CAP-123
- Exit criterion: `PRODUCTION_AND_PREVIEW_SURFACE_REACHABILITY_INVENTORIED`
- Contract: `docs/contracts/surface-reachability-inventory.v1.json`
- ADR: ADR-0118

## Current conclusion

The repository now has a complete machine-readable inventory for the known production, local, preview, deeplink and provider-callback surfaces.

**No production surface is externally verified.**

That conclusion is deliberate and evidence-based:

| Surface | Current state | What is actually proven |
| --- | --- | --- |
| Canonical API — local | `LOCAL_ONLY` | Localhost configuration exists. |
| Canonical API — production | `NOT_CONFIGURED` | No production HTTPS origin or external probe exists. |
| Admin Studio — local | `LOCAL_ONLY` | Local Next.js setup targets the local API. |
| Admin Studio — production | `NOT_CONFIGURED` | No deployed origin or operator access path exists. |
| Consumer web | `PLACEHOLDER_ONLY` | `apps/web` contains only its intent README. |
| Mobile production shell | `COMPILE_ONLY` | It builds against `https://beta-api.invalid/`; it is not usable production distribution. |
| Installable phone preview | `CI_ARTIFACT_AVAILABLE` | GitHub Actions creates a debug APK artifact from the explicit preview entrypoint. |
| `mobile-share-scheme-compile-candidate` | `COMPILE_ONLY` | MVP CI creates a transient Android host with hostless `kefe:` scheme, builds the production shell and deliberately does not upload the APK. |
| Mobile production deeplinks | `NOT_CONFIGURED` | In-app `/case/:caseId` routing exists, but no committed Android/iOS host declarations or association evidence exists. |
| Web deeplinks | `NOT_CONFIGURED` | No web runtime or externally probed canonical routes exist. |
| OTP provider receipt callback | `INTERNAL_ONLY` | The hidden HMAC callback route exists; no deployed provider/network binding exists. |

## Executable evidence

`services/api/tools/check_surface_reachability_inventory.py` verifies:

- the complete canonical surface set and allowed status/evidence catalogs;
- that only external HTTP/store/operator evidence can produce `REACHABLE_VERIFIED`;
- that `.invalid`, localhost, loopback, wildcard and emulator endpoints cannot be production reachability evidence;
- the compile-only production mobile endpoint;
- local mobile/Admin API defaults;
- consumer web placeholder-only state;
- in-app Case routing while distinguishing absent committed native deeplink hosts;
- the hostless, non-uploaded transient `kefe:` scheme compile candidate;
- the separately generated installable preview debug APK artifact;
- the internal-only, OpenAPI-hidden OTP provider callback;
- explicit next-proof requirements and non-claims for every surface.

Dedicated CI also reruns the phone artifact, production copy and OTP provider receipt parent contracts. It performs **No external reachability probe** and therefore cannot generate a deployment claim.

## Exit-criterion interpretation

This slice satisfies the **inventory** portion of `PRODUCTION_AND_PREVIEW_SURFACE_REACHABILITY_INVENTORIED`: every known surface has a current state, evidence class, repository source and next proof.

It does not make F4 production-ready. The following remain external or future gates:

1. production API provisioning and timestamped external route probes;
2. deployed consumer web and Admin Studio origins;
3. committed Android App Links, iOS Universal Links or approved custom-scheme declarations and association files;
4. controlled preview or store distribution evidence;
5. provider-bound callback reachability and availability evidence;
6. deployed SLO, incident response and operator-executed rollback evidence.

## Non-claims

- A CI artifact is not a public release or store distribution.
- A transient hostless `kefe:` scheme inserted into generated CI files is not committed production deeplink configuration.
- A successful build is not a reachable product surface.
- A local process is not a production deployment.
- An internal route is not proof that an external provider can reach it.
- The inventory does not prove availability, latency, SLO compliance, operator usability, recovery or rollback.
