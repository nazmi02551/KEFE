import 'package:flutter/foundation.dart';

enum VoiceDeliberationModeModel {
  audioBriefingReadout,
  anonymizedVoiceDictation,
  speechConfirmedVote,
}

@immutable
class VoiceDeliberationModel {
  const VoiceDeliberationModel({
    required this.sessionId,
    required this.mode,
    required this.audioDurationSeconds,
    required this.speechConfidenceScore,
    required this.isVoiceprintStripped,
    required this.transcriptPreview,
  });

  final String sessionId;
  final VoiceDeliberationModeModel mode;
  final double audioDurationSeconds;
  final double speechConfidenceScore;
  final bool isVoiceprintStripped;
  final String transcriptPreview;
}
