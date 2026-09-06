import 'package:flutter/foundation.dart';

enum EquilibriumStateModel {
  optimalBalance,
  highDeficitRisk,
  severeSocialImpact,
  environmentalDegradation,
}

@immutable
class PolicySimulatorModel {
  const PolicySimulatorModel({
    required this.simulationId,
    required this.caseVersionId,
    required this.policyKnobName,
    required this.knobValue,
    required this.fiscalScore,
    required this.socialScore,
    required this.environmentalScore,
    required this.equilibriumState,
  });

  final String simulationId;
  final String caseVersionId;
  final String policyKnobName;
  final double knobValue;
  final double fiscalScore;
  final double socialScore;
  final double environmentalScore;
  final EquilibriumStateModel equilibriumState;
}
