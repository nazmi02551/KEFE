import 'package:flutter/foundation.dart';

enum ConsequenceTypeModel {
  perverseIncentive,
  marketDistortion,
  behavioralRebound,
  systemicDisplacement,
}

enum ConsequenceSeverityModel {
  lowDrift,
  moderateImpact,
  severeParadox,
}

@immutable
class UnintendedConsequenceItemModel {
  const UnintendedConsequenceItemModel({
    required this.consequenceType,
    required this.severity,
    required this.mitigationFeasibility,
    required this.description,
  });

  final ConsequenceTypeModel consequenceType;
  final ConsequenceSeverityModel severity;
  final double mitigationFeasibility;
  final String description;
}

@immutable
class UnintendedConsequencesModel {
  const UnintendedConsequencesModel({
    required this.caseVersionId,
    required this.optionCode,
    required this.overallSystemicRisk,
    required this.consequences,
  });

  final String caseVersionId;
  final String optionCode;
  final ConsequenceSeverityModel overallSystemicRisk;
  final List<UnintendedConsequenceItemModel> consequences;
}
