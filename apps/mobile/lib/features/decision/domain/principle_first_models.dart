import 'package:flutter/foundation.dart';

enum PrincipleTypeModel {
  individualLiberty,
  collectiveWellbeing,
  proceduralJustice,
  empathyCompassion,
}

@immutable
class PrincipleFirstModel {
  const PrincipleFirstModel({
    required this.caseVersionId,
    required this.primaryPrinciple,
    required this.secondaryPrinciple,
    required this.consistencyScore,
    required this.reflectionPrompt,
  });

  final String caseVersionId;
  final PrincipleTypeModel primaryPrinciple;
  final PrincipleTypeModel secondaryPrinciple;
  final double consistencyScore;
  final String reflectionPrompt;
}
