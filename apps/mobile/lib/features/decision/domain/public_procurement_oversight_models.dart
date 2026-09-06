import 'package:flutter/foundation.dart';

enum ProcurementIntegrityLevelModel {
  openCompetitiveVerified,
  anomalousSoleSourceReview,
  criticalOverrunAlert,
}

@immutable
class ProcurementOversightModel {
  const ProcurementOversightModel({
    required this.tenderId,
    required this.contractingAuthority,
    required this.integrityLevel,
    required this.awardedAmountTry,
    required this.costOverrunPct,
    required this.activeCivicAuditorsCount,
  });

  final String tenderId;
  final String contractingAuthority;
  final ProcurementIntegrityLevelModel integrityLevel;
  final double awardedAmountTry;
  final double costOverrunPct;
  final int activeCivicAuditorsCount;
}
