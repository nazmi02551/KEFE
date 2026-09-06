import 'package:flutter/foundation.dart';

enum MunicipalProjectDomainModel {
  parksAndGreenSpaces,
  publicTransitAndMobility,
  educationAndYouthCenters,
  disasterResilienceAndSafety,
}

@immutable
class MunicipalBudgetProjectModel {
  const MunicipalBudgetProjectModel({
    required this.projectId,
    required this.municipalityName,
    required this.projectDomain,
    required this.requestedBudgetTry,
    required this.citizenVotesCount,
    required this.civicApprovalRate,
  });

  final String projectId;
  final String municipalityName;
  final MunicipalProjectDomainModel projectDomain;
  final int requestedBudgetTry;
  final int citizenVotesCount;
  final double civicApprovalRate;
}
