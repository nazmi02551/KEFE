import 'package:flutter/foundation.dart';

enum NgoAdvocacyDomainModel {
  humanRightsAndJustice,
  environmentAndClimate,
  publicHealthAndSafety,
  transparencyAndAntiCorruption,
}

@immutable
class NgoImpactDeskModel {
  const NgoImpactDeskModel({
    required this.campaignId,
    required this.ngoName,
    required this.advocacyDomain,
    required this.citizenEndorsementCount,
    required this.institutionalReformsAchieved,
    required this.advocacyEfficacyScore,
  });

  final String campaignId;
  final String ngoName;
  final NgoAdvocacyDomainModel advocacyDomain;
  final int citizenEndorsementCount;
  final int institutionalReformsAchieved;
  final double advocacyEfficacyScore;
}
