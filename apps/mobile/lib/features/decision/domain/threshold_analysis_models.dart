import 'package:flutter/foundation.dart';

@immutable
class SensitivityCurvePointModel {
  const SensitivityCurvePointModel({
    required this.parameterValue,
    required this.acceptanceRate,
  });

  final double parameterValue;
  final double acceptanceRate;
}

@immutable
class ThresholdAnalysisModel {
  const ThresholdAnalysisModel({
    required this.caseVersionId,
    required this.parameterName,
    required this.unit,
    required this.tippingPointThreshold,
    required this.curvePoints,
  });

  final String caseVersionId;
  final String parameterName;
  final String unit;
  final double tippingPointThreshold;
  final List<SensitivityCurvePointModel> curvePoints;
}
