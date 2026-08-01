import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Slice 23 contract locks presentation-only state convergence', () {
    final contract =
        jsonDecode(
              File(
                '../../docs/contracts/decision-flow-state-commit-slice23.v1.json',
              ).readAsStringSync(),
            )
            as Map<String, dynamic>;

    expect(contract['contract'], 'decision-flow-state-commit-slice23');
    expect(contract['scope']['decision_flow_presentation_convergence'], isTrue);
    expect(contract['scope']['decision_controller_change'], isFalse);
    expect(contract['scope']['repository_change'], isFalse);
    expect(contract['scope']['route_change'], isFalse);
    expect(contract['scope']['flow_order_change'], isFalse);

    expect(contract['root_states']['loading_deterministic'], isTrue);
    expect(
      contract['root_states']['loading_indeterminate_spinner_forbidden'],
      isTrue,
    );
    expect(
      contract['root_states']['transition_uses_kefe_motion_resolve'],
      isTrue,
    );

    expect(contract['commit_action']['stable_key'], 'commit-button');
    expect(contract['commit_action']['single_commit_action'], isTrue);
    expect(
      contract['commit_action']['required_response_gate_unchanged'],
      isTrue,
    );
    expect(contract['commit_action']['disabled_while_submitting'], isTrue);
    expect(
      contract['commit_action']['recovery_pending_uses_existing_retry_pending'],
      isTrue,
    );
    expect(contract['commit_action']['idempotency_change'], isFalse);
    expect(
      contract['commit_action']['submitting_indeterminate_spinner_forbidden'],
      isTrue,
    );

    expect(contract['flow_truth']['pre_commit_reveal_absent'], isTrue);
    expect(
      contract['flow_truth']['generic_primitive_dispatch_preserved'],
      isTrue,
    );
    expect(contract['invariants']['commit_first'], isTrue);
    expect(contract['invariants']['blind_first'], isTrue);
    expect(contract['invariants']['signal_in_scope'], isFalse);
    expect(contract['invariants']['impact_in_scope'], isFalse);
  });

  test(
    'governed Decision Flow source uses deterministic KEFE state surfaces',
    () {
      final source = File(
        'lib/features/decision/presentation/decision_flow_screen.dart',
      ).readAsStringSync();

      expect(source, contains('KefeMotion.resolve('));
      expect(source, contains("const ValueKey('decision-loading-surface')"));
      expect(source, contains("const ValueKey('decision-error-surface')"));
      expect(source, contains("const ValueKey('decision-status-surface')"));
      expect(source, contains("const ValueKey('decision-status-message')"));
      expect(source, contains("const ValueKey('commit-button')"));
      expect(source, contains("ValueKey('capability-pending-\${step.code}')"));

      expect(source, isNot(contains('CircularProgressIndicator')));
      expect(source, isNot(contains('return Card(')));
      expect(
        source,
        isNot(contains('duration: const Duration(milliseconds: 220)')),
      );
      expect(source, isNot(contains('item.id ==')));
      expect(source, isNot(contains('caseData.title ==')));
    },
  );

  test('Commit enablement and recovery dispatch remain source-locked', () {
    final source = File(
      'lib/features/decision/presentation/decision_flow_screen.dart',
    ).readAsStringSync();

    expect(source, contains('!state.hasRequiredResponses || state.submitting'));
    expect(source, contains('state.recoveryPending'));
    expect(source, contains('controller.retryPending'));
    expect(source, contains('controller.commit'));
    expect(
      source,
      contains("'COLLECTIVE_RESULT' => _resultStep(context, ref)"),
    );
    expect(source, contains('state.reveal == null'));
  });
}
