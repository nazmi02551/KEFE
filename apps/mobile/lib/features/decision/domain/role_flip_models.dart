import 'package:flutter/foundation.dart';

@immutable
class RoleFlipModel {
  const RoleFlipModel({
    required this.caseVersionId,
    required this.initialRole,
    required this.flippedRole,
    required this.flippedScenarioPrompt,
    required this.perspectiveShiftScore,
  });

  final String caseVersionId;
  final String initialRole;
  final String flippedRole;
  final String flippedScenarioPrompt;
  final double perspectiveShiftScore;
}
