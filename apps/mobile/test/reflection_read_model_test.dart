import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/features/decision/domain/reflection_models.dart';

void main() {
  test('ReflectionReadModel parses only the bounded server projection', () {
    final model = ReflectionReadModel.fromJson(const {
      'session_id': 'session-1',
      'case_version_id': 'case-version-1',
      'flow_step_code': 'REFLECTION',
      'revision_count': 2,
      'latest_revision_id': 'revision-2',
      'latest_delta_id': 'delta-1',
      'decision_changed': true,
      'changed_question_count': 1,
      'intervention_count': 2,
      'intervention_type_codes': ['CONTEXT_REVEAL', 'SOURCE_EXPOSURE'],
      'from_contribution_class': 'CORE_PRE_RESULT',
      'to_contribution_class': 'EXPOSED',
      'completed': false,
    });

    expect(model.sessionId, 'session-1');
    expect(model.caseVersionId, 'case-version-1');
    expect(model.flowStepCode, 'REFLECTION');
    expect(model.revisionCount, 2);
    expect(model.latestRevisionId, 'revision-2');
    expect(model.latestDeltaId, 'delta-1');
    expect(model.decisionChanged, isTrue);
    expect(model.changedQuestionCount, 1);
    expect(model.interventionCount, 2);
    expect(model.interventionTypeCodes, ['CONTEXT_REVEAL', 'SOURCE_EXPOSURE']);
    expect(model.fromContributionClass, 'CORE_PRE_RESULT');
    expect(model.toContributionClass, 'EXPOSED');
    expect(model.completed, isFalse);
  });

  test('ReflectionReadModel keeps optional delta and completion semantics', () {
    final model = ReflectionReadModel.fromJson(const {
      'session_id': 'session-2',
      'case_version_id': 'case-version-2',
      'flow_step_code': 'REFLECTION',
      'revision_count': 1,
      'latest_revision_id': 'revision-1',
      'latest_delta_id': null,
      'decision_changed': false,
      'changed_question_count': 0,
      'intervention_count': 0,
      'intervention_type_codes': [],
      'from_contribution_class': null,
      'to_contribution_class': 'CORE_PRE_RESULT',
      'completed': true,
    });

    expect(model.latestDeltaId, isNull);
    expect(model.fromContributionClass, isNull);
    expect(model.decisionChanged, isFalse);
    expect(model.completed, isTrue);
  });
}
