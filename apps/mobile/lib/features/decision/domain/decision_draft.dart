import 'package:flutter/foundation.dart';

@immutable
class DecisionDraft {
  const DecisionDraft({
    required this.caseId,
    required this.caseVersionId,
    required this.sessionId,
    required this.questionId,
    required this.selectedOption,
    required this.updatedAt,
    this.commitIdempotencyKey,
    this.commitPending = false,
  });

  final String caseId;
  final String caseVersionId;
  final String sessionId;
  final String questionId;
  final String selectedOption;
  final String? commitIdempotencyKey;
  final bool commitPending;
  final DateTime updatedAt;

  DecisionDraft copyWith({
    String? selectedOption,
    String? commitIdempotencyKey,
    bool? commitPending,
    DateTime? updatedAt,
  }) {
    return DecisionDraft(
      caseId: caseId,
      caseVersionId: caseVersionId,
      sessionId: sessionId,
      questionId: questionId,
      selectedOption: selectedOption ?? this.selectedOption,
      commitIdempotencyKey: commitIdempotencyKey ?? this.commitIdempotencyKey,
      commitPending: commitPending ?? this.commitPending,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  Map<String, Object?> toJson() => {
    'case_id': caseId,
    'case_version_id': caseVersionId,
    'session_id': sessionId,
    'question_id': questionId,
    'selected_option': selectedOption,
    'commit_idempotency_key': commitIdempotencyKey,
    'commit_pending': commitPending,
    'updated_at': updatedAt.toUtc().toIso8601String(),
  };

  factory DecisionDraft.fromJson(Map<String, Object?> json) {
    return DecisionDraft(
      caseId: json['case_id'] as String,
      caseVersionId: json['case_version_id'] as String,
      sessionId: json['session_id'] as String,
      questionId: json['question_id'] as String,
      selectedOption: json['selected_option'] as String,
      commitIdempotencyKey: json['commit_idempotency_key'] as String?,
      commitPending: json['commit_pending'] as bool? ?? false,
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }
}
