import 'package:flutter/foundation.dart';

enum CulturalNormDimensionModel {
  communitySolidarityAndMutuality,
  individualAutonomyAndLiberty,
  intergenerationalStewardship,
  proceduralJusticeAndEquity,
}

@immutable
class CulturalNormModel {
  const CulturalNormModel({
    required this.frameworkId,
    required this.regionIdentifier,
    required this.primaryDimension,
    required this.culturalAlignmentScore,
    required this.universalBaselineCompliance,
    required this.normSynthesisSummary,
  });

  final String frameworkId;
  final String regionIdentifier;
  final CulturalNormDimensionModel primaryDimension;
  final double culturalAlignmentScore;
  final bool universalBaselineCompliance;
  final String normSynthesisSummary;
}
