# Privacy self-service cross-surface boundary

The deterministic export and deletion hardening keeps the existing API privacy authority at `GET /v1/me/privacy-export` and `DELETE /v1/me`.

- It adds no consumer/mobile write endpoint beyond the existing authenticated deletion command.
- Mobile receives no private export cache, archive store, background job, browser/device persistence or secondary user profile.
- Actor identity remains server-derived and deletion confirmation is bound to that exact authenticated actor.
- Export verification metadata is descriptive only and contains no personality, ideology, psychometric, morality, bias, causal, normative or social-worth inference.
- Commit First, Blind First, immutable CaseVersion, My KEFE descriptive history and Product Preview/production isolation remain unchanged.
- CI phone artifacts are compile/upload evidence only, not a production release, legal-compliance proof or store submission.
