import 'package:flutter/foundation.dart';

import 'decision_models.dart';

enum DecisionDraftPhase {
  editing,
  commitPending,
  committedAwaitingReveal,
}

@immutable
class DecisionDraft {
  const DecisionDraft({
    required this.caseData,
    required this.sessionId,
    required this.questionId,
    required this.selectedOption,
    required this.updatedAt,
    this.commitIdempotencyKey,
    this.phase = DecisionDraftPhase.editing,
  });

  final DecisionCase caseData;
  final String sessionId;
  final String questionId;
  final String selectedOption;
  final String? commitIdempotencyKey;
  final DecisionDraftPhase phase;
  final DateTime updatedAt;

  String get caseId => caseData.id;
  String get caseVersionId => caseData.versionId;

  DecisionDraft copyWith({
    String? selectedOption,
    String? commitIdempotencyKey,
    DecisionDraftPhase? phase,
    DateTime? updatedAt,
  }) {
    return DecisionDraft(
      caseData: caseData,
      sessionId: sessionId,
      questionId: questionId,
      selectedOption: selectedOption ?? this.selectedOption,
      commitIdempotencyKey: commitIdempotencyKey ?? this.commitIdempotencyKey,
      phase: phase ?? this.phase,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  Map<String, Object?> toJson() => {
    'case': {
      'id': caseData.id,
      'version_id': caseData.versionId,
      'title': caseData.title,
      'summary': caseData.summary,
      'format': caseData.format,
      'domain': caseData.domain,
      'risk': caseData.risk,
      'questions': caseData.questions
          .map(
            (question) => {
              'id': question.id,
              'prompt': question.prompt,
              'response_type': question.responseType,
              'options': question.options,
            },
          )
          .toList(growable: false),
    },
    'session_id': sessionId,
    'question_id': questionId,
    'selected_option': selectedOption,
    'commit_idempotency_key': commitIdempotencyKey,
    'phase': phase.name,
    'updated_at': updatedAt.toUtc().toIso8601String(),
  };

  factory DecisionDraft.fromJson(Map<String, Object?> json) {
    final caseJson = (json['case'] as Map).cast<String, Object?>();
    final questions = (caseJson['questions'] as List<Object?>)
        .cast<Map>()
        .map((raw) {
          final question = raw.cast<String, Object?>();
          return DecisionQuestion(
            id: question['id'] as String,
            prompt: question['prompt'] as String,
            responseType: question['response_type'] as String,
            options: (question['options'] as List<Object?>).cast<String>(),
          );
        })
        .toList(growable: false);

    final rawPhase = json['phase'] as String? ?? DecisionDraftPhase.editing.name;
    final phase = DecisionDraftPhase.values.firstWhere(
      (value) => value.name == rawPhase,
      orElse: () => DecisionDraftPhase.editing,
    );

    return DecisionDraft(
      caseData: DecisionCase(
        id: caseJson['id'] as String,
        versionId: caseJson['version_id'] as String,
        title: caseJson['title'] as String,
        summary: caseJson['summary'] as String,
        format: caseJson['format'] as String,
        domain: caseJson['domain'] as String,
        risk: caseJson['risk'] as String,
        questions: questions,
      ),
      sessionId: json['session_id'] as String,
      questionId: json['question_id'] as String,
      selectedOption: json['selected_option'] as String,
      commitIdempotencyKey: json['commit_idempotency_key'] as String?,
      phase: phase,
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }
}
