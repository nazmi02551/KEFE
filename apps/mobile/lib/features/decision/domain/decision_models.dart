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
class DecisionQuestion {
  const DecisionQuestion({
    required this.id,
    required this.prompt,
    required this.responseType,
    required this.options,
  });

  final String id;
  final String prompt;
  final String responseType;
  final List<String> options;
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
