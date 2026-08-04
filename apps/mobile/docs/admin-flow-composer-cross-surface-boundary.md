# Admin Flow Composer cross-surface boundary

## Scope

The Admin Flow Composer is an internal DRAFT-only control-plane surface. It edits versioned Flow Template definitions inside the existing `ContentConfigurationSnapshot` authority.

## Mobile and consumer boundary

This slice changes no mobile route, screen, copy, navigation, Decision response contract or consumer Flow execution rule.

Consumer runtime continues to:

- read the immutable `resolved_flow` pinned into a published `CaseVersion`;
- avoid live Content Configuration lookups during a weigh session;
- preserve Commit First and applicable Blind First/pre-result isolation;
- expose no Admin DRAFT, unpublished configuration or Flow Composer state;
- use no Preview fixture as a production fallback.

A Flow Composer save remains a configuration `DRAFT` operation. It does not publish the configuration, repin a CaseVersion, mutate an existing weigh session or alter a production consumer response.

## CI meaning

Mobile CI, MVP Beta Gates and Global Readiness are required regression and compile evidence because the generic Flow contract is cross-surface infrastructure. APK artifacts produced by those workflows are proof artifacts only and are not a new user release.

These checks do not prove human editorial usability, production deployment, store compliance, signing, rollout, operator rollback or deployed SLO/load/observability.
