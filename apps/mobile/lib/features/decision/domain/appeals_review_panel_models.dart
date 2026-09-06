import 'package:flutter/foundation.dart';

enum AppealVerdictModel {
  overturnedRestored,
  upheldViolationConfirmed,
  partialRevisionPermitted,
}

@immutable
class AppealsReviewModel {
  const AppealsReviewModel({
    required this.appealId,
    required this.targetResourceId,
    required this.appealVerdict,
    required this.panelistCount,
    required this.favorRatio,
    required this.resolutionSummary,
  });

  final String appealId;
  final String targetResourceId;
  final AppealVerdictModel appealVerdict;
  final int panelistCount;
  final double favorRatio;
  final String resolutionSummary;
}
