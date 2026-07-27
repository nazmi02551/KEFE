import 'package:flutter/foundation.dart';

@immutable
class GuestCredential {
  const GuestCredential({
    required this.actorId,
    required this.accessToken,
    required this.expiresAt,
  });

  final String actorId;
  final String accessToken;
  final DateTime expiresAt;
}

@immutable
class DecisionCaseSummary {
  const DecisionCaseSummary({
    required this.id,
    required this.versionId,
    required this.title,
    required this.summary,
    required this.format,
    required this.domain,
    required this.risk,
  });

  final String id;
  final String versionId;
  final String title;
  final String summary;
  final String format;
  final String domain;
  final String risk;
}

@immutable
class DecisionQuestion {
  const DecisionQuestion({
    required this.id,
    required this.prompt,
    required this.responseType,
    this.required = true,
    this.options = const [],
    this.responseSchema = const {},
  });

  final String id;
  final String prompt;
  final String responseType;
  final bool required;
  final List<String> options;
  final Map<String, Object?> responseSchema;

  double get minimum => (responseSchema['min'] as num?)?.toDouble() ?? 1;
  double get maximum => (responseSchema['max'] as num?)?.toDouble() ?? 5;
  double get step => (responseSchema['step'] as num?)?.toDouble() ?? 1;
}

@immutable
class DecisionCase {
  const DecisionCase({
    required this.id,
    required this.versionId,
    required this.title,
    required this.summary,
    required this.format,
    required this.domain,
    required this.risk,
    required this.questions,
  });

  final String id;
  final String versionId;
  final String title;
  final String summary;
  final String format;
  final String domain;
  final String risk;
  final List<DecisionQuestion> questions;
}

@immutable
class RevealResult {
  const RevealResult({
    required this.layer,
    required this.sampleSize,
    required this.confidence,
    required this.values,
  });

  final String layer;
  final int sampleSize;
  final String confidence;
  final Map<String, double> values;
}
