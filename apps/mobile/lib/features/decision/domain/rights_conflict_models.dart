import 'package:flutter/foundation.dart';

enum RightsCollisionTypeModel {
  privacyVsSecurity,
  expressionVsDignity,
  propertyVsEnvironment,
  individualLibertyVsPublicHealth,
}

enum RestrictionSeverityModel {
  permissibleRestriction,
  coreRightErosion,
  unconstitutionalBreach,
}

@immutable
class RightsConflictModel {
  const RightsConflictModel({
    required this.caseVersionId,
    required this.optionCode,
    required this.collisionType,
    required this.severity,
    required this.inalienableCoreScore,
    required this.constitutionalRationale,
  });

  final String caseVersionId;
  final String optionCode;
  final RightsCollisionTypeModel collisionType;
  final RestrictionSeverityModel severity;
  final double inalienableCoreScore;
  final String constitutionalRationale;
}
