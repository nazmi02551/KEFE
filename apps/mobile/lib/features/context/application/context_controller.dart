import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../decision/application/decision_controller.dart';
import '../../decision/data/decision_repository.dart';
import '../../decision/data/http_decision_repository.dart';
import '../data/context_repository.dart';
import '../domain/context_models.dart';

class ContextState {
  const ContextState({
    this.loading = false,
    this.snapshot,
    this.errorCode,
  });

  final bool loading;
  final CaseContextSnapshot? snapshot;
  final String? errorCode;
}

final contextControllerProvider = NotifierProvider.autoDispose
    .family<ContextController, ContextState, String>(ContextController.new);

class ContextController extends AutoDisposeFamilyNotifier<ContextState, String> {
  DecisionRepository get _repository => ref.read(decisionRepositoryProvider);

  @override
  ContextState build(String caseVersionId) {
    Future.microtask(load);
    return const ContextState(loading: true);
  }

  Future<void> load() async {
    state = const ContextState(loading: true);
    try {
      final snapshot = await _repository.fetchContext(arg);
      state = ContextState(snapshot: snapshot);
    } on ClientTransportFailure catch (error) {
      state = ContextState(errorCode: error.code);
    } on ApiFailure catch (error) {
      state = ContextState(errorCode: error.code);
    } catch (_) {
      state = const ContextState(errorCode: 'UNEXPECTED_CLIENT_ERROR');
    }
  }
}
