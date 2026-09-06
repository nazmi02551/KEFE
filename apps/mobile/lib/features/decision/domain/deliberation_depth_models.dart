import 'package:flutter/foundation.dart';

enum DepthLevelModel {
  profoundDeliberation,
  structuredReflection,
  superficialSkimming,
}

@immutable
class DeliberationDepthModel {
  const DeliberationDepthModel({
    required this.caseVersionId,
    required this.deliberationDepthScore,
    required this.depthLevel,
    required this.argumentsInspectedCount,
    required this.evidenceItemsVerifiedCount,
    required this.counterViewsExploredCount,
  });

  final String caseVersionId;
  final double deliberationDepthScore;
  final DepthLevelModel depthLevel;
  final int argumentsInspectedCount;
  final int evidenceItemsVerifiedCount;
  final int counterViewsExploredCount;
}
