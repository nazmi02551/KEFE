import 'package:flutter/foundation.dart';

enum ArgumentStrengthTierModel {
  tierARobust,
  tierBPlausible,
  tierCWeakRhetorical,
}

@immutable
class ArgumentStrengthModel {
  const ArgumentStrengthModel({
    required this.argumentId,
    required this.empiricalFoundationScore,
    required this.logicalConsistencyScore,
    required this.representativeBalanceScore,
    required this.compositeStrengthScore,
    required this.strengthTier,
  });

  final String argumentId;
  final double empiricalFoundationScore;
  final double logicalConsistencyScore;
  final double representativeBalanceScore;
  final double compositeStrengthScore;
  final ArgumentStrengthTierModel strengthTier;
}
