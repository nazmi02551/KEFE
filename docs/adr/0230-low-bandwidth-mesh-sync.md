# ADR-0230: Low-Bandwidth Offline Mesh & Delay-Tolerant Sync (CAP-084)

## Status

ACCEPTED

## Context

In disaster zones, rural geographies with intermittent 2G/3G connectivity, or amidst state internet shutdowns, citizens must be able to deliberate locally over peer-to-peer Bluetooth/Wi-Fi Direct mesh networks and sync cryptographically signed weigh receipts upon reconnecting. Under `KEFE-PB-001`, `KEFE-ETG-001`, and `KEFE-ENG-001`, KEFE provides a Low-Bandwidth Delay-Tolerant Mesh Sync module.

## Decision

1. **Sync Network Channel Taxonomy**:
   - `PEER_BLUETOOTH_DIRECT_MESH`: Local peer-to-peer hop relay.
   - `COMPRESSED_DELAY_TOLERANT_BUNDLE`: High-compression CBOR/gzip batch payload for 2G uplink.
   - `FULL_BROADBAND_RECONCILED`: Canonical cloud epoch sync confirmed.
2. **Cryptographic Nonce Invariant**:
   - Every mesh-relayed receipt contains immutable cryptographic signatures and replay prevention nonces.

## Consequences

- Guarantees censorship-resistant, disaster-proof democratic participation.
- Enables seamless operation across the most remote rural and disconnected regions.
