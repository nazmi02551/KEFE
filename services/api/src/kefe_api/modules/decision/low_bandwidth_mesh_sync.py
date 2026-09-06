from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MeshSyncChannel(StrEnum):
    PEER_BLUETOOTH_DIRECT_MESH = "PEER_BLUETOOTH_DIRECT_MESH"
    COMPRESSED_DELAY_TOLERANT_BUNDLE = "COMPRESSED_DELAY_TOLERANT_BUNDLE"
    FULL_BROADBAND_RECONCILED = "FULL_BROADBAND_RECONCILED"


@dataclass(frozen=True, slots=True)
class MeshSyncResult:
    bundle_id: str
    network_channel: MeshSyncChannel
    queued_receipts_count: int
    compressed_payload_bytes: int
    sync_compression_ratio: float
    is_replay_guarded: bool


class LowBandwidthMeshSyncService:
    @staticmethod
    def prepare_sync_bundle(
        *,
        bundle_id: str,
        network_channel: MeshSyncChannel,
        queued_receipts_count: int,
        raw_payload_bytes: int,
    ) -> MeshSyncResult:
        if queued_receipts_count < 0:
            raise ValueError("queued_receipts_count cannot be negative")
        if raw_payload_bytes < 64:
            raise ValueError(f"raw_payload_bytes must be >= 64, got {raw_payload_bytes}")

        # CBOR/gzip compression simulation
        compressed_bytes = max(64, int(raw_payload_bytes * 0.22))
        compression_ratio = compressed_bytes / raw_payload_bytes

        return MeshSyncResult(
            bundle_id=bundle_id.strip(),
            network_channel=network_channel,
            queued_receipts_count=queued_receipts_count,
            compressed_payload_bytes=compressed_bytes,
            sync_compression_ratio=round(compression_ratio, 2),
            is_replay_guarded=True,
        )
