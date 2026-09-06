import 'package:flutter/foundation.dart';

enum DivergenceDriverTypeModel {
  normativeValueWeight,
  factualProbabilityAssessment,
  proceduralGovernance,
  timeHorizon,
}

@immutable
class DivergenceDriverItemModel {
  const DivergenceDriverItemModel({
    required this.driverType,
    required this.sharePercentage,
    required this.explanation,
  });

  final DivergenceDriverTypeModel driverType;
  final double sharePercentage;
  final String explanation;
}

@immutable
class DivergenceAnatomyModel {
  const DivergenceAnatomyModel({
    required this.caseVersionId,
    required this.primaryDriver,
    required this.drivers,
  });

  final String caseVersionId;
  final DivergenceDriverTypeModel primaryDriver;
  final List<DivergenceDriverItemModel> drivers;
}
