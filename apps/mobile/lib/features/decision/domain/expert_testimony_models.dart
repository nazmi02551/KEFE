import 'package:flutter/foundation.dart';

enum TestimonyArchetypeModel {
  independentAcademicExpert,
  governmentalRegulatoryBody,
  industryCorporateStakeholder,
  civilSocietyAdvocate,
}

enum EpistemicAuthorityTierModel {
  highPeerReviewed,
  officialRegulatory,
  partisanSpecialInterest,
}

@immutable
class ExpertTestimonyModel {
  const ExpertTestimonyModel({
    required this.testimonyId,
    required this.sourceName,
    required this.archetype,
    required this.conflictOfInterestScore,
    required this.epistemicAuthorityTier,
    required this.testimonyStatement,
  });

  final String testimonyId;
  final String sourceName;
  final TestimonyArchetypeModel archetype;
  final double conflictOfInterestScore;
  final EpistemicAuthorityTierModel epistemicAuthorityTier;
  final String testimonyStatement;
}
