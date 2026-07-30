# Phone Candidate Artifact Boundary — 2026-07-30

The artifact produced by `MVP Beta Gates` from `lib/main.dart` is a production-entry isolation/build artifact. It intentionally uses a non-routable beta API origin and is not the installable phone usability candidate.

Installable internal phone candidates must be built from the explicit Product Preview entrypoint and labeled as internal/preview. Production must continue to fail closed rather than silently use preview fixtures.
