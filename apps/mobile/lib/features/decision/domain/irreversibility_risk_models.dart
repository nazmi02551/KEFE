import 'package:flutter/foundation.dart';

enum ReversibilityClassModel {
  fullyReversible,
  conditionallyReversible,
  substantiallyIrreversible,
  permanentlyIrreversible,
}

@immutable
class IrreversibilityRiskModel {
  const IrreversibilityRiskModel({
    required this.caseVersionId,
    required this.optionCode,
    required this.reversibilityClass,
    required this.precautionaryRiskScore,
    required this.unwindTimeMonths,
    required this.unwindCostFactor,
    required this.riskSummary,
  });

  final String caseVersionId;
  final String optionCode;
  final ReversibilityClassModel reversibilityClass;
  final double precautionaryRiskScore;
  final int unwindTimeMonths;
  final double unwindCostFactor;
  final String riskSummary;
}
