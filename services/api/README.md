# KEFE API

FastAPI modular monolith. Capability modules own their domain/application behavior and expose declared ports. Infrastructure/provider adapters remain outside domain code.

Initial bootstrap exposes only `/health`; the first business vertical slice will add `Case → Weigh → Commit → Reveal` using the versioned contracts under `docs/contracts`.
