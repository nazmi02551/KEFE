import 'package:flutter/foundation.dart';

enum MigrationEpochTypeModel {
  initialBlindResonance,
  midDeliberationShift,
  maturedConsensusState,
}

@immutable
class TemporalOpinionFlowModel {
  const TemporalOpinionFlowModel({
    required this.flowId,
    required this.caseVersionId,
    required this.epochType,
    required this.optionAShare,
    required this.optionBShare,
    required this.undecidedBridgeShare,
    required this.migrationRate,
  });

  final String flowId;
  final String caseVersionId;
  final MigrationEpochTypeModel epochType;
  final double optionAShare;
  final double optionBShare;
  final double undecidedBridgeShare;
  final double migrationRate;
}
