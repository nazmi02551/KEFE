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
    this.isRealEvent = false,
  });

  final String id;
  final String versionId;
  final String title;
  final String summary;
  final String format;
  final String domain;
  final String risk;
  final bool isRealEvent;
}

enum PublicCaseVersionClassification { current, previous }

@immutable
class PublicCaseVersion {
  const PublicCaseVersion({
    required this.versionId,
    required this.versionNo,
    required this.title,
    required this.summary,
    required this.publishedAt,
    required this.classification,
  });

  final String versionId;
  final int versionNo;
  final String title;
  final String summary;
  final DateTime? publishedAt;
  final PublicCaseVersionClassification classification;

  bool get isCurrent =>
      classification == PublicCaseVersionClassification.current;
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
      maxTags: rawMaxTags is int ? rawMaxTags.clamp(1, 10).toInt() : 3,
      textEnabled: schema['text_enabled'] == true,
      textMaxLength: rawTextMaxLength is int
          ? rawTextMaxLength.clamp(1, 1000).toInt()
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

enum FlowExecutionSupport { full, partial }

enum FlowStepRuntimeState { ready, completed, blocked, unsupported }

@immutable
class FlowRuntimeStep {
  const FlowRuntimeStep({
    required this.code,
    required this.primitiveCode,
    required this.capabilityCodes,
    required this.nextStepCodes,
    required this.state,
    this.reasonCode,
  });

  final String code;
  final String primitiveCode;
  final List<String> capabilityCodes;
  final List<String> nextStepCodes;
  final FlowStepRuntimeState state;
  final String? reasonCode;

  bool get isRenderable =>
      state == FlowStepRuntimeState.ready ||
      state == FlowStepRuntimeState.completed ||
      state == FlowStepRuntimeState.unsupported;

  Map<String, Object?> toJson() => {
    'code': code,
    'primitive_code': primitiveCode,
    'capability_codes': capabilityCodes,
    'next_step_codes': nextStepCodes,
    'state': state.name.toUpperCase(),
    'reason_code': reasonCode,
  };

  factory FlowRuntimeStep.fromJson(Map<String, Object?> json) {
    return FlowRuntimeStep(
      code: json['code'] as String,
      primitiveCode: json['primitive_code'] as String,
      capabilityCodes: (json['capability_codes'] as List<Object?>? ?? const [])
          .map((value) => value.toString())
          .toList(growable: false),
      nextStepCodes: (json['next_step_codes'] as List<Object?>? ?? const [])
          .map((value) => value.toString())
          .toList(growable: false),
      state: switch (json['state']) {
        'READY' => FlowStepRuntimeState.ready,
        'COMPLETED' => FlowStepRuntimeState.completed,
        'BLOCKED' => FlowStepRuntimeState.blocked,
        'UNSUPPORTED' => FlowStepRuntimeState.unsupported,
        _ => FlowStepRuntimeState.unsupported,
      },
      reasonCode: json['reason_code'] as String?,
    );
  }
}

@immutable
class FlowRuntimeSnapshot {
  const FlowRuntimeSnapshot({
    required this.sessionId,
    required this.caseVersionId,
    required this.sessionState,
    required this.templateCode,
    required this.templateVersionNo,
    required this.entryStepCode,
    required this.executionSupport,
    required this.steps,
  });

  final String sessionId;
  final String caseVersionId;
  final String sessionState;
  final String templateCode;
  final int templateVersionNo;
  final String entryStepCode;
  final FlowExecutionSupport executionSupport;
  final List<FlowRuntimeStep> steps;

  bool matches({required String sessionId, required String caseVersionId}) =>
      this.sessionId == sessionId && this.caseVersionId == caseVersionId;

  Map<String, Object?> toJson() => {
    'session_id': sessionId,
    'case_version_id': caseVersionId,
    'session_state': sessionState,
    'template_code': templateCode,
    'template_version_no': templateVersionNo,
    'entry_step_code': entryStepCode,
    'execution_support': executionSupport.name.toUpperCase(),
    'steps': steps.map((step) => step.toJson()).toList(growable: false),
  };

  factory FlowRuntimeSnapshot.fromJson(Map<String, Object?> json) {
    return FlowRuntimeSnapshot(
      sessionId: json['session_id'] as String,
      caseVersionId: json['case_version_id'] as String,
      sessionState: json['session_state'] as String,
      templateCode: json['template_code'] as String,
      templateVersionNo: json['template_version_no'] as int,
      entryStepCode: json['entry_step_code'] as String,
      executionSupport: json['execution_support'] == 'FULL'
          ? FlowExecutionSupport.full
          : FlowExecutionSupport.partial,
      steps: (json['steps'] as List<Object?>)
          .cast<Map>()
          .map((raw) => FlowRuntimeStep.fromJson(raw.cast<String, Object?>()))
          .toList(growable: false),
    );
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

enum PerspectiveUiState {
  idle,
  loading,
  ready,
  clusterPending,
  degradedCurated,
  errorRetryable,
}

enum PerspectiveSlot { near, opposing, bridge, alternativeContext }

@immutable
class PerspectiveCard {
  const PerspectiveCard({
    required this.id,
    required this.slot,
    required this.body,
    required this.sourceKind,
    required this.provenanceLabel,
    required this.moderationState,
  });

  final String id;
  final PerspectiveSlot slot;
  final String body;
  final String sourceKind;
  final String provenanceLabel;
  final String moderationState;
}

@immutable
class PerspectiveMethodology {
  const PerspectiveMethodology({
    required this.mode,
    required this.sampleKind,
    required this.sampleSize,
    required this.generatedAt,
    required this.provenanceNote,
  });

  final String mode;
  final String sampleKind;
  final int sampleSize;
  final DateTime generatedAt;
  final String provenanceNote;
}

@immutable
class PerspectiveResult {
  const PerspectiveResult({
    required this.sessionId,
    required this.caseVersionId,
    required this.cards,
    required this.methodology,
  });

  final String sessionId;
  final String caseVersionId;
  final List<PerspectiveCard> cards;
  final PerspectiveMethodology methodology;

  PerspectiveUiState get uiState => switch (methodology.mode) {
    'READY' => PerspectiveUiState.ready,
    'CLUSTER_PENDING' => PerspectiveUiState.clusterPending,
    'DEGRADED_CURATED' => PerspectiveUiState.degradedCurated,
    _ => PerspectiveUiState.errorRetryable,
  };
}
