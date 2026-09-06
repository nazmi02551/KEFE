import 'package:flutter/foundation.dart';

enum YouthSpaceFocusAreaModel {
  campusAndEducationPolicy,
  climateAndIntergenerational,
  digitalRightsAndAi,
  civicEntrepreneurship,
}

@immutable
class YouthDeliberationSpaceModel {
  const YouthDeliberationSpaceModel({
    required this.spaceId,
    required this.spaceName,
    required this.focusArea,
    required this.institutionOrCommunity,
    required this.activeStudentCount,
    required this.consensusActionCount,
  });

  final String spaceId;
  final String spaceName;
  final YouthSpaceFocusAreaModel focusArea;
  final String institutionOrCommunity;
  final int activeStudentCount;
  final int consensusActionCount;
}
