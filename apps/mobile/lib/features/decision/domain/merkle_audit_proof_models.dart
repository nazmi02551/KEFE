import 'package:flutter/foundation.dart';

enum MerkleProofStatusModel {
  inclusionVerified,
  consistencyProven,
  proofChallengedTampered,
}

@immutable
class MerkleAuditProofModel {
  const MerkleAuditProofModel({
    required this.leafId,
    required this.rootEpochId,
    required this.merkleRootHash,
    required this.proofDepth,
    required this.status,
    required this.verifiedTimestamp,
  });

  final String leafId;
  final String rootEpochId;
  final String merkleRootHash;
  final int proofDepth;
  final MerkleProofStatusModel status;
  final String verifiedTimestamp;
}
