import 'package:flutter/foundation.dart';

enum FallacyTypeModel {
  adHominem,
  strawMan,
  falseDilemma,
  slipperySlope,
  appealToEmotionFear,
  noFallacyDetected,
}

@immutable
class DetectedFallacyItemModel {
  const DetectedFallacyItemModel({
    required this.fallacyType,
    required this.confidence,
    required this.explanation,
  });

  final FallacyTypeModel fallacyType;
  final double confidence;
  final String explanation;
}

@immutable
class FallacyDetectionResultModel {
  const FallacyDetectionResultModel({
    required this.argumentId,
    required this.hasFallacy,
    required this.overallIntegrityScore,
    required this.detectedFallacies,
  });

  final String argumentId;
  final bool hasFallacy;
  final double overallIntegrityScore;
  final List<DetectedFallacyItemModel> detectedFallacies;
}
