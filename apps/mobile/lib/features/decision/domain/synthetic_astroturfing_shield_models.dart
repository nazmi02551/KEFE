import 'package:flutter/foundation.dart';

enum BotDefenseStateModel {
  organicCitizenAuthentic,
  suspectedBotCoordination,
  isolatedQuarantineSwarm,
}

@immutable
class BotShieldModel {
  const BotShieldModel({
    required this.clusterId,
    required this.targetCaseId,
    required this.defenseState,
    required this.syntheticProbabilityScore,
    required this.quarantinedBotPayloadsCount,
    required this.semanticEntropyIndex,
  });

  final String clusterId;
  final String targetCaseId;
  final BotDefenseStateModel defenseState;
  final double syntheticProbabilityScore;
  final int quarantinedBotPayloadsCount;
  final double semanticEntropyIndex;
}
