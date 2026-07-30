import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../decision/application/decision_controller.dart';
import '../../decision/data/decision_repository.dart';
import '../../decision/data/http_decision_repository.dart';
import '../../decision/domain/decision_models.dart';

class ExploreState {
  const ExploreState({
    this.loading = false,
    this.items = const [],
    this.errorCode,
  });

  final bool loading;
  final List<DecisionCaseSummary> items;
  final String? errorCode;
}

final exploreControllerProvider =
    NotifierProvider<ExploreController, ExploreState>(ExploreController.new);

class ExploreController extends Notifier<ExploreState> {
  DecisionRepository get _repository => ref.read(decisionRepositoryProvider);

  @override
  ExploreState build() => const ExploreState();

  Future<void> load() async {
    state = const ExploreState(loading: true);
    try {
      final items = await _repository.fetchExploreCases();
      state = ExploreState(items: items);
    } on ClientTransportFailure catch (error) {
      state = ExploreState(errorCode: error.code);
    } on ApiFailure catch (error) {
      state = ExploreState(errorCode: error.code);
    } catch (_) {
      state = const ExploreState(errorCode: 'UNEXPECTED_CLIENT_ERROR');
    }
  }
}
