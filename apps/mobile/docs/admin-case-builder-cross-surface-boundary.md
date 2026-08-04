# Admin Case Builder cross-surface boundary

The Admin Case Builder DRAFT workspace is an internal operations surface over the existing Content Authoring aggregate.

This slice does **not** change:

- consumer Case, CaseVersion, FlowStep or Decision contracts;
- Commit First / Blind First behavior;
- mobile navigation, rendering or phone persistence;
- production/preview isolation;
- My KEFE descriptive-history semantics;
- installable phone artifact identity.

Mobile CI, MVP Beta Gates and Global Readiness still run on the exact child head to prove that the additive Admin adapter and UI introduce no consumer or phone regression. A green compile/test artifact is repository evidence only; it is not a new production APK release.
