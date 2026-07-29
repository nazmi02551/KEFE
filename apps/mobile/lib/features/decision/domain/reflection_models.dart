import 'package:flutter/foundation.dart';

@immutable
class ReflectionReadModel {
  const ReflectionReadModel({
    required this.sessionId,
    required this.caseVersionId,
    required this.flowStepCode,
    required this.revisionCount,
    required this.latestRevisionId,
    required this.decisionChanged,
    required this.changedQuestionCount,
    required this.interventionCount,
    required this.interventionTypeCodes,
    required this.toContributionClass,
    required this.completed,
    this.latestDeltaId,
    this.fromContributionClass,
  });

  final String sessionId;
  final String caseVersionId;
  final String flowStepCode;
  final int revisionCount;
  final String latestRevisionId;
  final String? latestDeltaId;
  final bool decisionChanged;
  final int changedQuestionCount;
  final int interventionCount;
  final List<String> interventionTypeCodes;
  final String? fromContributionClass;
  final String toContributionClass;
  final bool completed;

  ReflectionReadModel copyWith({bool? completed}) {
    return ReflectionReadModel(
      sessionId: sessionId,
      caseVersionId: caseVersionId,
      flowStepCode: flowStepCode,
      revisionCount: revisionCount,
      latestRevisionId: latestRevisionId,
      latestDeltaId: latestDeltaId,
      decisionChanged: decisionChanged,
      changedQuestionCount: changedQuestionCount,
      interventionCount: interventionCount,
      interventionTypeCodes: interventionTypeCodes,
      fromContributionClass: fromContributionClass,
      toContributionClass: toContributionClass,
      completed: completed ?? this.completed,
    );
  }

  factory ReflectionReadModel.fromJson(Map<String, Object?> json) {
    return ReflectionReadModel(
      sessionId: json['session_id'] as String,
      caseVersionId: json['case_version_id'] as String,
      flowStepCode: json['flow_step_code'] as String,
      revisionCount: json['revision_count'] as int,
      latestRevisionId: json['latest_revision_id'] as String,
      latestDeltaId: json['latest_delta_id'] as String?,
      decisionChanged: json['decision_changed'] as bool,
      changedQuestionCount: json['changed_question_count'] as int,
      interventionCount: json['intervention_count'] as int,
      interventionTypeCodes:
          (json['intervention_type_codes'] as List<Object?>? ?? const [])
              .map((value) => value.toString())
              .toList(growable: false),
      fromContributionClass: json['from_contribution_class'] as String?,
      toContributionClass: json['to_contribution_class'] as String,
      completed: json['completed'] as bool? ?? false,
    );
  }
}
