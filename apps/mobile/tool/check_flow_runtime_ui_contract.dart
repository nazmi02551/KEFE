import 'dart:io';

void main() {
  final repoRoot = Directory.current.parent.parent;
  final contract = File(
    '${repoRoot.path}/docs/contracts/mobile-flow-runtime-ui.v1.yaml',
  ).readAsStringSync();
  final controller = File(
    '${Directory.current.path}/lib/features/decision/application/decision_controller.dart',
  ).readAsStringSync();
  final screen = File(
    '${Directory.current.path}/lib/features/decision/presentation/decision_flow_screen.dart',
  ).readAsStringSync();
  final repository = File(
    '${Directory.current.path}/lib/features/decision/data/http_decision_repository.dart',
  ).readAsStringSync();
  final draft = File(
    '${Directory.current.path}/lib/features/decision/domain/decision_draft.dart',
  ).readAsStringSync();

  final problems = <String>[];

  for (final fragment in <String>{
    'fixed_screen_fallback_for_flow_session: forbidden',
    'client_case_type_branching: forbidden',
    'draft_persists_flow_snapshot: true',
    'refresh_flow_runtime_after_commit: true',
    'result_payload_from_flow_runtime: forbidden',
  }) {
    if (!contract.contains(fragment)) {
      problems.add('Mobile Flow UI contract missing: $fragment');
    }
  }

  for (final fragment in <String>{
    'fetchFlowRuntime(draft.sessionId)',
    'fetchFlowRuntime(sessionId)',
    'flowRuntime: flowRuntime',
    "'FLOW_RUNTIME_OFFLINE_UNAVAILABLE'",
  }) {
    if (!controller.contains(fragment)) {
      problems.add('DecisionController Flow behavior missing: $fragment');
    }
  }

  for (final fragment in <String>{
    'for (final step in flowRuntime.steps)',
    "'CONTEXT' => _contextStep()",
    "'DECISION' => _decisionStep(context, ref)",
    "'COLLECTIVE_RESULT' => _resultStep(context, ref)",
    '_CapabilityPendingCard',
  }) {
    if (!screen.contains(fragment)) {
      problems.add('DecisionFlowScreen Flow rendering missing: $fragment');
    }
  }

  for (final forbidden in <String>{
    'caseData.format ==',
    'switch (caseData.format)',
    'airline_child_case',
    'political_insult_case',
    'site_park_case',
  }) {
    if (screen.contains(forbidden) || controller.contains(forbidden)) {
      problems.add('Case-specific mobile branching is forbidden: $forbidden');
    }
  }

  if (!repository.contains('/v1/weigh-sessions/\$sessionId/flow')) {
    problems.add('HTTP repository does not call the Flow runtime endpoint');
  }
  if (!draft.contains("'flow_runtime': flowRuntime?.toJson()")) {
    problems.add('DecisionDraft does not persist Flow runtime continuity state');
  }

  if (problems.isNotEmpty) {
    stderr.writeln(problems.join('\n'));
    exitCode = 1;
    return;
  }

  stdout.writeln(
    'Mobile Flow UI contract OK: server Step rendering, offline Flow continuity, '
    'no fixed/case-specific fallback verified.',
  );
}
