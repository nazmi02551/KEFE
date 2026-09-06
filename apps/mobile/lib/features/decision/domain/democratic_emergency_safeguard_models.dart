import 'package:flutter/foundation.dart';

enum EmergencySafeguardStatusModel {
  proportionateSunsetBounded,
  sunsetExpirationApproaching,
  authoritarianCreepViolation,
}

@immutable
class DemocraticEmergencyModel {
  const DemocraticEmergencyModel({
    required this.decreeId,
    required this.emergencyJurisdiction,
    required this.safeguardStatus,
    required this.proportionalityScore,
    required this.remainingSunsetDays,
  });

  final String decreeId;
  final String emergencyJurisdiction;
  final EmergencySafeguardStatusModel safeguardStatus;
  final double proportionalityScore;
  final int remainingSunsetDays;
}
