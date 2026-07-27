# Infrastructure

Infrastructure is organized around environment-neutral modules, ordered PostgreSQL migrations, observability/SLO definitions and security policy-as-code.

Provider-specific bindings remain replaceable infrastructure concerns and must not leak into domain logic.
