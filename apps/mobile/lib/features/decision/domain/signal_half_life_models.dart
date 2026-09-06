import 'package:flutter/foundation.dart';

enum FreshnessStateModel {
  fresh,
  stable,
  deprecating,
  expiredNeedsRetest,
}

@immutable
class SignalHalfLifeModel {
  const SignalHalfLifeModel({
    required this.signalId,
    required this.caseVersionId,
    required this.halfLifeDays,
    required this.ageDays,
    required this.remainingWeight,
    required this.freshnessState,
  });

  final String signalId;
  final String caseVersionId;
  final int halfLifeDays;
  final double ageDays;
  final double remainingWeight;
  final FreshnessStateModel freshnessState;
}
