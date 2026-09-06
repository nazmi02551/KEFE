import 'package:flutter/foundation.dart';

enum BridgeEfficacyStateModel {
  highDepolarization,
  moderateBridgeResonance,
  persistentPolarization,
}

@immutable
class DepolarizationIndexModel {
  const DepolarizationIndexModel({
    required this.caseVersionId,
    required this.preDeliberationDistance,
    required this.postDeliberationDistance,
    required this.depolarizationScore,
    required this.bridgeEfficacyState,
  });

  final String caseVersionId;
  final double preDeliberationDistance;
  final double postDeliberationDistance;
  final double depolarizationScore;
  final BridgeEfficacyStateModel bridgeEfficacyState;
}
