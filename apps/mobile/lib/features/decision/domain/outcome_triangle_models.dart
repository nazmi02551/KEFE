import 'package:flutter/foundation.dart';

enum TriangleArchetypeModel {
  rightsCentric,
  empathyCentric,
  utilityCentric,
  triBalancedHarmony,
}

@immutable
class OutcomeTriangleModel {
  const OutcomeTriangleModel({
    required this.caseVersionId,
    required this.optionCode,
    required this.rulesWeight,
    required this.empathyWeight,
    required this.utilityWeight,
    required this.dominantArchetype,
  });

  final String caseVersionId;
  final String optionCode;
  final double rulesWeight;
  final double empathyWeight;
  final double utilityWeight;
  final TriangleArchetypeModel dominantArchetype;
}
