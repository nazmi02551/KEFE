from __future__ import annotations

from kefe_api.modules.decision.low_bandwidth_mesh_sync import (
    LowBandwidthMeshSyncService,
    MeshSyncChannel,
    MeshSyncResult,
)


def test_mesh_sync_prepares_compressed_bundle() -> None:
    r = LowBandwidthMeshSyncService.prepare_sync_bundle(
        bundle_id="msh_001",
        network_channel=MeshSyncChannel.COMPRESSED_DELAY_TOLERANT_BUNDLE,
        queued_receipts_count=45,
        raw_payload_bytes=10240,
    )

    assert isinstance(r, MeshSyncResult)
    assert r.network_channel == MeshSyncChannel.COMPRESSED_DELAY_TOLERANT_BUNDLE
    assert r.queued_receipts_count == 45
    assert r.compressed_payload_bytes == 2252
    assert r.sync_compression_ratio == 0.22
    assert r.is_replay_guarded is True


def test_mesh_sync_invalid_payload() -> None:
    failed = False
    try:
        LowBandwidthMeshSyncService.prepare_sync_bundle(
            bundle_id="msh_002",
            network_channel=MeshSyncChannel.PEER_BLUETOOTH_DIRECT_MESH,
            queued_receipts_count=-1,  # < 0
            raw_payload_bytes=32,  # < 64
        )
    except ValueError:
        failed = True

    assert failed is True
