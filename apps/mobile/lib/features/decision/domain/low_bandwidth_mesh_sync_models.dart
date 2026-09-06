import 'package:flutter/foundation.dart';

enum MeshSyncChannelModel {
  peerBluetoothDirectMesh,
  compressedDelayTolerantBundle,
  fullBroadbandReconciled,
}

@immutable
class MeshSyncModel {
  const MeshSyncModel({
    required this.bundleId,
    required this.networkChannel,
    required this.queuedReceiptsCount,
    required this.compressedPayloadBytes,
    required this.syncCompressionRatio,
    required this.isReplayGuarded,
  });

  final String bundleId;
  final MeshSyncChannelModel networkChannel;
  final int queuedReceiptsCount;
  final int compressedPayloadBytes;
  final double syncCompressionRatio;
  final bool isReplayGuarded;
}
