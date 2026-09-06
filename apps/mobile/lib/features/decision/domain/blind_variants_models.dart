import 'package:flutter/foundation.dart';

enum BlindModeModel {
  actorBlind,
  sourceBlind,
  outcomeBlind,
}

@immutable
class BlindVariantsModel {
  const BlindVariantsModel({
    required this.caseVersionId,
    required this.blindMode,
    required this.blindedPrompt,
    required this.realIdentityRevealed,
    required this.neutralityScore,
  });

  final String caseVersionId;
  final BlindModeModel blindMode;
  final String blindedPrompt;
  final String realIdentityRevealed;
  final double neutralityScore;
}
