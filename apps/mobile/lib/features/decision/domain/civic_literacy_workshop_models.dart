import 'package:flutter/foundation.dart';

enum LiteracyModuleTypeModel {
  fallacySpotting,
  ethicalFrameworks,
  evidenceEvaluation,
  bridgeSynthesis,
}

@immutable
class CivicLiteracyWorkshopModel {
  const CivicLiteracyWorkshopModel({
    required this.workshopId,
    required this.moduleType,
    required this.moduleTitle,
    required this.totalDrills,
    required this.completedDrills,
    required this.comprehensionScore,
  });

  final String workshopId;
  final LiteracyModuleTypeModel moduleType;
  final String moduleTitle;
  final int totalDrills;
  final int completedDrills;
  final double comprehensionScore;
}
