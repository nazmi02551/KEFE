import 'package:flutter/foundation.dart';

enum SimilarityAlignmentTierModel {
  highTopologicalAnalogue,
  partialDomainOverlap,
  distantPrecedent,
}

@immutable
class CrossCaseSimilarityModel {
  const CrossCaseSimilarityModel({
    required this.sourceCaseId,
    required this.targetCaseId,
    required this.targetCaseTitle,
    required this.similarityScore,
    required this.alignmentTier,
    required this.sharedTensionSummary,
  });

  final String sourceCaseId;
  final String targetCaseId;
  final String targetCaseTitle;
  final double similarityScore;
  final SimilarityAlignmentTierModel alignmentTier;
  final String sharedTensionSummary;
}
