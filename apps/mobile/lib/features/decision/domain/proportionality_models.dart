import 'package:flutter/foundation.dart';

enum ProportionalityOutcomeModel {
  proportionalValid,
  excessivelyBurdensome,
  disproportionateInvalid,
}

@immutable
class ProportionalityTestModel {
  const ProportionalityTestModel({
    required this.caseVersionId,
    required this.optionCode,
    required this.compositeProportionalityScore,
    required this.outcome,
    required this.suitabilityScore,
    required this.necessityLeastIntrusiveScore,
    required this.strictProportionalityScore,
    required this.summary,
  });

  final String caseVersionId;
  final String optionCode;
  final double compositeProportionalityScore;
  final ProportionalityOutcomeModel outcome;
  final double suitabilityScore;
  final double necessityLeastIntrusiveScore;
  final double strictProportionalityScore;
  final String summary;
}
