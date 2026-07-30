import 'package:flutter/foundation.dart';

import 'decision_models.dart';

enum DecisionDraftPhase {
  editing,
  syncPending,
  commitPending,
  committedAwaitingReveal,
}

@immutable
class DecisionDraft {
  const DecisionDraft({
    required this.caseData,
    required this.sessionId,
    required this.updatedAt,
    this.flowRuntime,
    this.flowStepCode,
    this.responses = const {},
    this.reasonTags = const [],
    this.reasonText,
    this.questionId,
    this.selectedOption,
    this.commitIdempotencyKey,
    this.phase = DecisionDraftPhase.editing,
  });

  final DecisionCase caseData;
  final String sessionId;
  final FlowRuntimeSnapshot? flowRuntime;
  final String? flowStepCode;
  final Map<String, Object?> responses;
  final List<String> reasonTags;
  final String? reasonText;

  // Legacy fields are kept only to migrate v2 single-answer drafts safely.
  final String? questionId;
  final String? selectedOption;

  final String? commitIdempotencyKey;
  final DecisionDraftPhase phase;
  final DateTime updatedAt;

  String get caseId => caseData.id;
  String get caseVersionId => caseData.versionId;

  Map<String, Object?> get effectiveResponses {
    if (responses.isNotEmpty) return responses;
    if (questionId != null && selectedOption != null) {
      return {questionId!: selectedOption};
    }
    return const {};
  }

  DecisionDraft copyWith({
    FlowRuntimeSnapshot? flowRuntime,
    String? flowStepCode,
    bool clearFlowStepCode = false,
    Map<String, Object?>? responses,
    List<String>? reasonTags,
    String? reasonText,
    bool clearReasonText = false,
    String? commitIdempotencyKey,
    DecisionDraftPhase? phase,
    DateTime? updatedAt,
  }) {
    return DecisionDraft(
      caseData: caseData,
      sessionId: sessionId,
      flowRuntime: flowRuntime ?? this.flowRuntime,
      flowStepCode: clearFlowStepCode
          ? null
          : flowStepCode ?? this.flowStepCode,
      responses: responses ?? effectiveResponses,
      reasonTags: reasonTags ?? this.reasonTags,
      reasonText: clearReasonText ? null : reasonText ?? this.reasonText,
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
              'required': question.required,
              'options': question.options,
              'response_schema': question.responseSchema,
            },
          )
          .toList(growable: false),
    },
    'session_id': sessionId,
    'flow_runtime': flowRuntime?.toJson(),
    'flow_step_code': flowStepCode,
    'responses': effectiveResponses,
    'reason_tags': reasonTags,
    'reason_text': reasonText,
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
            required: question['required'] as bool? ?? true,
            options: (question['options'] as List<Object?>? ?? const [])
                .cast<String>(),
            responseSchema:
                (question['response_schema'] as Map?)
                    ?.cast<String, Object?>() ??
                const {},
          );
        })
        .toList(growable: false);

    final rawPhase =
        json['phase'] as String? ?? DecisionDraftPhase.editing.name;
    final phase = DecisionDraftPhase.values.firstWhere(
      (value) => value.name == rawPhase,
      orElse: () => DecisionDraftPhase.editing,
    );

    final rawResponses = json['responses'];
    final responses = rawResponses is Map
        ? rawResponses.cast<String, Object?>()
        : <String, Object?>{
            if (json['question_id'] case final String questionId)
              questionId: json['selected_option'],
          };

    final rawFlow = json['flow_runtime'];
    final flowRuntime = rawFlow is Map
        ? FlowRuntimeSnapshot.fromJson(rawFlow.cast<String, Object?>())
        : null;

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
      flowRuntime: flowRuntime,
      flowStepCode: json['flow_step_code'] as String?,
      responses: responses,
      reasonTags: (json['reason_tags'] as List<Object?>? ?? const [])
          .cast<String>(),
      reasonText: json['reason_text'] as String?,
      commitIdempotencyKey: json['commit_idempotency_key'] as String?,
      phase: phase,
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }
}
