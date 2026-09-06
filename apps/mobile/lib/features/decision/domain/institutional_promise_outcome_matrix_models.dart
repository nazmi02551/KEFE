import 'package:flutter/foundation.dart';

enum PromiseRealizationStatusModel {
  promiseDeliveredVerified,
  inProgressOnTrack,
  promiseBrokenDefault,
}

@immutable
class PromiseOutcomeModel {
  const PromiseOutcomeModel({
    required this.matrixId,
    required this.institutionName,
    required this.promiseTitle,
    required this.realizationStatus,
    required this.milestoneCompletionPct,
    required this.empiricalEvidenceArtifactsCount,
  });

  final String matrixId;
  final String institutionName;
  final String promiseTitle;
  final PromiseRealizationStatusModel realizationStatus;
  final double milestoneCompletionPct;
  final int empiricalEvidenceArtifactsCount;
}
