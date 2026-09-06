import 'package:flutter/foundation.dart';

enum LobbyingExposureLevelModel {
  cleanIndependentDisclosure,
  declaredStakeholderFinancing,
  highConflictExposureAlert,
}

@immutable
class LobbyingRadarModel {
  const LobbyingRadarModel({
    required this.radarId,
    required this.organizationId,
    required this.exposureLevel,
    required this.transparencyIndex,
    required this.declaredFundingAmountUsd,
    required this.primaryBenefactorSector,
  });

  final String radarId;
  final String organizationId;
  final LobbyingExposureLevelModel exposureLevel;
  final double transparencyIndex;
  final double declaredFundingAmountUsd;
  final String primaryBenefactorSector;
}
