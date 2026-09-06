import 'package:flutter/foundation.dart';

enum VulnerableCohortModel {
  childrenYouth,
  elderlyGeriatric,
  lowIncomeImpoverished,
  personsWithDisabilities,
  minorityMarginalized,
}

enum ProtectionStatusModel {
  strongProtectiveFloor,
  neutralNoDisproportion,
  severeDisproportionateBurden,
}

@immutable
class CohortEvaluationItemModel {
  const CohortEvaluationItemModel({
    required this.cohort,
    required this.impactScore,
    required this.assessment,
  });

  final VulnerableCohortModel cohort;
  final double impactScore;
  final String assessment;
}

@immutable
class VulnerableGroupsShieldModel {
  const VulnerableGroupsShieldModel({
    required this.caseVersionId,
    required this.optionCode,
    required this.overallProtectionStatus,
    required this.safetyNetFloorScore,
    required this.cohortEvaluations,
  });

  final String caseVersionId;
  final String optionCode;
  final ProtectionStatusModel overallProtectionStatus;
  final double safetyNetFloorScore;
  final List<CohortEvaluationItemModel> cohortEvaluations;
}
