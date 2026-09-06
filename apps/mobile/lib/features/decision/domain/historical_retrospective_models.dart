import 'package:flutter/foundation.dart';

enum HistoricalEraModel {
  ancientClassical,
  industrialEra,
  twentiethCentury,
  contemporaryCrisis,
}

@immutable
class HistoricalRetrospectiveModel {
  const HistoricalRetrospectiveModel({
    required this.retrospectiveId,
    required this.caseVersionId,
    required this.historicalEra,
    required this.historicalYear,
    required this.historicalEventName,
    required this.actualHistoricalDecision,
    required this.historicalConsequenceSummary,
  });

  final String retrospectiveId;
  final String caseVersionId;
  final HistoricalEraModel historicalEra;
  final int historicalYear;
  final String historicalEventName;
  final String actualHistoricalDecision;
  final String historicalConsequenceSummary;
}
