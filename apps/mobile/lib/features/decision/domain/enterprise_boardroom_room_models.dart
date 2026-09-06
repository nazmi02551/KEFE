import 'package:flutter/foundation.dart';

enum BoardroomDilemmaScopeModel {
  esgAndSustainability,
  capitalAllocationAndMa,
  executiveCompensation,
  crisisManagement,
}

@immutable
class EnterpriseBoardroomModel {
  const EnterpriseBoardroomModel({
    required this.roomId,
    required this.organizationName,
    required this.dilemmaScope,
    required this.boardMemberCount,
    required this.fiduciaryConsensusRatio,
    required this.esgAlignmentScore,
  });

  final String roomId;
  final String organizationName;
  final BoardroomDilemmaScopeModel dilemmaScope;
  final int boardMemberCount;
  final double fiduciaryConsensusRatio;
  final double esgAlignmentScore;
}
