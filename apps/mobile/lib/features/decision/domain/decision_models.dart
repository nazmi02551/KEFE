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
class ReasonPolicy {
  const ReasonPolicy({
    required this.tags,
    required this.maxTags,
    required this.textEnabled,
    required this.textMaxLength,
  });

  final List<String> tags;
  final int maxTags;
  final bool textEnabled;
  final int textMaxLength;

  bool get enabled => tags.isNotEmpty || textEnabled;

  factory ReasonPolicy.fromSchema(Map<String, Object?> schema) {
    final tags = (schema['tags'] as List<Object?>? ?? const [])
        .map((value) => value.toString())
        .where((value) => value.isNotEmpty)
        .toList(growable: false);
    final rawMaxTags = schema['max_tags'];
    final rawTextMaxLength = schema['text_max_length'];
    return ReasonPolicy(
      tags: tags,
      maxTags: rawMaxTags is int ? rawMaxTags.clamp(1, 10) : 3,
      textEnabled: schema['text_enabled'] == true,
      textMaxLength: rawTextMaxLength is int
          ? rawTextMaxLength.clamp(1, 1000)
          : 500,
    );
  }
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

  ReasonPolicy? get reasonPolicy {
    for (final question in questions) {
      final raw = question.responseSchema['reason'];
      if (raw is Map) {
        final policy = ReasonPolicy.fromSchema(raw.cast<String, Object?>());
        if (policy.enabled) return policy;
      }
    }
    return null;
  }
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
