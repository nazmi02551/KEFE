import 'package:flutter/foundation.dart';

enum CounterfactualConditionTypeModel {
  empiricalDataThreshold,
  vulnerabilityProtection,
  economicSustainability,
  moralImpasseEmpathy,
  unconditionalStance,
}

enum EpistemicFlexibilityClassModel {
  highlyEpistemicOpen,
  conditionallyFlexible,
  categoricalAbsolute,
}

@immutable
class SelectedCounterfactualConditionModel {
  const SelectedCounterfactualConditionModel({
    required this.conditionType,
    required this.description,
  });

  final CounterfactualConditionTypeModel conditionType;
  final String description;
}

@immutable
class ChangeMindInquiryModel {
  const ChangeMindInquiryModel({
    required this.caseVersionId,
    required this.selectedConditions,
    required this.flexibilityClass,
    this.customFalsificationNote,
  });

  final String caseVersionId;
  final List<SelectedCounterfactualConditionModel> selectedConditions;
  final EpistemicFlexibilityClassModel flexibilityClass;
  final String? customFalsificationNote;
}
