# ADR-0088 — Strict bounded RSS/Atom parsing profile

Status: Accepted
Date: 2026-08-03
Issue: #236
Parent: PR #228 / ADR-0087

## Context

KEFE can now govern public provider execution without fake credentials, but no public feed body may be interpreted until XML parsing has an explicit hostile-input boundary. General-purpose feed libraries often accept broader XML, extension namespaces, entity behavior or implicit recovery than KEFE needs.

## Decision

Introduce a provider-neutral, network-free parser supporting only RSS 2.0 and Atom 1.0 documents.

The parser:

1. accepts an immutable byte document and an explicit limits profile;
2. rejects empty or oversized documents before XML parsing;
3. rejects DTD, ENTITY declarations, processing instructions and XInclude markers before tree construction;
4. uses the Python standard-library XML parser without network, filesystem or external entity hooks;
5. enforces maximum element depth, total element count, entry count and normalized text length;
6. accepts only exact RSS 2.0 `rss/channel/item` and Atom 1.0 namespace `feed/entry` roots;
7. returns immutable normalized feed and entry metadata only;
8. normalizes whitespace deterministically and preserves no executable markup;
9. does not infer truth, authority, jurisdiction, language, editorial acceptance or publication readiness;
10. maps malformed, unsupported and limit failures to bounded final error codes.

Required entry identity is the first non-blank value from RSS `guid` then `link`, or Atom `id` then alternate `link href`. Entries without identity are rejected. Dates remain bounded source strings in this slice; date interpretation is a later contract.

## Consequences

- RSS/Atom parsing can be tested without live network access.
- XXE-style declarations and parser expansion surfaces fail closed.
- Extension data is ignored rather than trusted.
- A later adapter may combine controlled public HTTP capture, durable raw evidence and this parser.

## Non-claims

No concrete feed, endpoint allowlist, live request, provider approval, HTML sanitizer, date semantics, scheduling, automatic proposal creation, editorial acceptance, publication or phone-facing behavior is introduced.