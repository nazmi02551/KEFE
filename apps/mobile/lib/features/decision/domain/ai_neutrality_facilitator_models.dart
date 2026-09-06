import 'package:flutter/foundation.dart';

enum FacilitationModeModel {
  socraticInquiryPrompt,
  nonviolentReframingSynthesis,
  commonGroundSurfacing,
}

@immutable
class FacilitationModel {
  const FacilitationModel({
    required this.interventionId,
    required this.deliberationRoomId,
    required this.mode,
    required this.neutralityIndex,
    required this.deescalationEfficacyScore,
    required this.facilitationPromptText,
  });

  final String interventionId;
  final String deliberationRoomId;
  final FacilitationModeModel mode;
  final double neutralityIndex;
  final double deescalationEfficacyScore;
  final String facilitationPromptText;
}
