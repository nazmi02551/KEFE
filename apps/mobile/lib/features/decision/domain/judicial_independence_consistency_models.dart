import 'package:flutter/foundation.dart';

enum JurisprudentialConsistencyStatusModel {
  precedentAlignedConsistent,
  discretionaryDeviationNoticed,
  executiveInterferenceSuspected,
}

@immutable
class JudicialConsistencyModel {
  const JudicialConsistencyModel({
    required this.chamberId,
    required this.courtJurisdiction,
    required this.caseCategory,
    required this.consistencyStatus,
    required this.precedentFidelityScore,
    required this.evaluatedPrecedentCasesCount,
  });

  final String chamberId;
  final String courtJurisdiction;
  final String caseCategory;
  final JurisprudentialConsistencyStatusModel consistencyStatus;
  final double precedentFidelityScore;
  final int evaluatedPrecedentCasesCount;
}
