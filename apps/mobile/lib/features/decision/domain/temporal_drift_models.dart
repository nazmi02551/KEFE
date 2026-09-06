import 'package:flutter/foundation.dart';

enum DriftNatureModel {
  stableConviction,
  maturedRevision,
  exploratoryShift,
  reinforcedCertainty,
}

@immutable
class TemporalDriftModel {
  const TemporalDriftModel({
    required this.caseVersionId,
    required this.initialOptionCode,
    required this.retestOptionCode,
    required this.timeElapsedDays,
    required this.isShifted,
    required this.confidenceDelta,
    required this.driftNature,
  });

  final String caseVersionId;
  final String initialOptionCode;
  final String retestOptionCode;
  final int timeElapsedDays;
  final bool isShifted;
  final double confidenceDelta;
  final DriftNatureModel driftNature;
}
