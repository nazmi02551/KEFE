# Admin Case Media cross-surface boundary

The Admin Case Media Registry is a provider-neutral production metadata and exact CaseVersion binding authority.

- It does not add or alter any consumer/mobile write endpoint.
- It does not change CaseVersion authoring, review, approval, publication, Flow pinning, Commit, Reveal, My KEFE, Atlas or Community Reason behavior.
- Product Preview keeps its packaged local `PreviewCaseMediaRepository`; those fixture assets are review-only and can never become production fallback.
- The production projection returns only READY assets bound to the exact CaseVersion and remains empty when no separately configured delivery resolver/provider is available.
- `delivery_ref` is opaque metadata. It is not a public URL, signed URL, credential, provider SDK object, bucket key or evidence that bytes are uploaded or globally reachable.
- No binary upload, multipart body, object-store/CDN SDK, image transformation, video transcode, autoplay, DRM, malware scan or automatic Case binding/publication is added to mobile.
- No user, author, reporter, decision-session, account or device identity is added to media responses.
- No personality, ideology, psychometric, morality, bias, causal or normative inference is produced.
- Mobile and Global CI artifacts remain compile/upload evidence only. They are not a release APK, production deployment, store submission, provider activation, external availability proof, deployed SLO or rollback validation.
