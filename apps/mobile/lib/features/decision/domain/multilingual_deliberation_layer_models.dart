import 'package:flutter/foundation.dart';

enum TranslationFidelityTierModel {
  highFidelityCertified,
  communityVerified,
  machineRawPreview,
}

@immutable
class MultilingualTranslationModel {
  const MultilingualTranslationModel({
    required this.translationId,
    required this.sourceLocale,
    required this.targetLocale,
    required this.fidelityTier,
    required this.semanticSimilarityScore,
    required this.translatedText,
  });

  final String translationId;
  final String sourceLocale;
  final String targetLocale;
  final TranslationFidelityTierModel fidelityTier;
  final double semanticSimilarityScore;
  final String translatedText;
}
