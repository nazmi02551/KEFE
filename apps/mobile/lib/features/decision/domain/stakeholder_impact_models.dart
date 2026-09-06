import 'package:flutter/foundation.dart';

enum StakeholderGroupTypeModel {
  directUsers,
  workers,
  vulnerableGroups,
  taxpayers,
  futureGenerations,
}

enum StakeholderImpactTypeModel {
  benefit,
  burden,
  neutral,
  protection,
}

@immutable
class StakeholderImpactItemModel {
  const StakeholderImpactItemModel({
    required this.group,
    required this.impactType,
    required this.impactScore,
    required this.description,
  });

  final StakeholderGroupTypeModel group;
  final StakeholderImpactTypeModel impactType;
  final int impactScore;
  final String description;
}

@immutable
class StakeholderImpactMatrixModel {
  const StakeholderImpactMatrixModel({
    required this.caseVersionId,
    required this.optionCode,
    required this.impactItems,
    required this.netEquityScore,
  });

  final String caseVersionId;
  final String optionCode;
  final List<StakeholderImpactItemModel> impactItems;
  final int netEquityScore;
}
