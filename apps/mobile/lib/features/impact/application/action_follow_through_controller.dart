import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/action_follow_through_repository.dart';
import '../domain/action_follow_through_models.dart';

class ActionFollowThroughState {
  const ActionFollowThroughState({
    this.loading = false,
    this.actions = const [],
    this.errorCode,
  });

  final bool loading;
  final List<ActionFollowThroughItem> actions;
  final String? errorCode;
}

final actionFollowThroughControllerProvider =
    NotifierProvider<
      ActionFollowThroughController,
      ActionFollowThroughState
    >(ActionFollowThroughController.new);

class ActionFollowThroughController
    extends Notifier<ActionFollowThroughState> {
  ActionFollowThroughRepository get _repository =>
      ref.read(actionFollowThroughRepositoryProvider);

  @override
  ActionFollowThroughState build() {
    Future.microtask(load);
    return const ActionFollowThroughState(loading: true);
  }

  Future<void> load({String? caseVersionId}) async {
    state = const ActionFollowThroughState(loading: true);
    try {
      final actions = await _repository.fetchActions(
        caseVersionId: caseVersionId,
      );
      state = ActionFollowThroughState(actions: actions);
    } catch (_) {
      state = const ActionFollowThroughState(
        errorCode: 'FAILED_TO_LOAD_ACTIONS',
      );
    }
  }

  Future<void> proposeAction({
    required String caseVersionId,
    required String title,
    required String description,
    DateTime? targetCompletionDate,
  }) async {
    try {
      final item = await _repository.proposeAction(
        caseVersionId: caseVersionId,
        title: title,
        description: description,
        targetCompletionDate: targetCompletionDate,
      );
      state = ActionFollowThroughState(actions: [...state.actions, item]);
    } catch (_) {
      state = const ActionFollowThroughState(
        errorCode: 'FAILED_TO_PROPOSE_ACTION',
      );
    }
  }
}
