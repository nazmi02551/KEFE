import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../decision/application/decision_controller.dart';
import '../../decision/data/decision_repository.dart';
import '../../decision/data/http_decision_repository.dart';
import '../data/http_progress_repository.dart';
import '../data/progress_repository.dart';
import '../domain/progress_models.dart';

final progressRepositoryProvider = Provider<ProgressRepository>((ref) {
  return HttpProgressRepository(
    config: ref.watch(appConfigProvider),
    client: ref.watch(httpClientProvider),
    credentialStore: ref.watch(credentialStoreProvider),
  );
});

enum ProgressUiState { idle, loading, ready, errorRetryable }

class ProgressState {
  const ProgressState({
    this.uiState = ProgressUiState.idle,
    this.envelope,
    this.errorCode,
    this.offerDismissed = false,
  });

  final ProgressUiState uiState;
  final ProgressEnvelope? envelope;
  final String? errorCode;
  final bool offerDismissed;

  ProgressState copyWith({
    ProgressUiState? uiState,
    ProgressEnvelope? envelope,
    String? errorCode,
    bool? offerDismissed,
    bool clearError = false,
  }) {
    return ProgressState(
      uiState: uiState ?? this.uiState,
      envelope: envelope ?? this.envelope,
      errorCode: clearError ? null : errorCode ?? this.errorCode,
      offerDismissed: offerDismissed ?? this.offerDismissed,
    );
  }
}

final progressControllerProvider =
    NotifierProvider<ProgressController, ProgressState>(ProgressController.new);

class ProgressController extends Notifier<ProgressState> {
  ProgressRepository get _repository => ref.read(progressRepositoryProvider);

  @override
  ProgressState build() => const ProgressState();

  Future<void> load() async {
    if (state.uiState == ProgressUiState.loading) return;
    state = state.copyWith(uiState: ProgressUiState.loading, clearError: true);
    try {
      final envelope = await _repository.fetchProgress();
      state = state.copyWith(
        uiState: ProgressUiState.ready,
        envelope: envelope,
        clearError: true,
      );
    } on ClientTransportFailure catch (error) {
      state = state.copyWith(
        uiState: ProgressUiState.errorRetryable,
        errorCode: error.code,
      );
    } on ApiFailure catch (error) {
      state = state.copyWith(
        uiState: ProgressUiState.errorRetryable,
        errorCode: error.code,
      );
    } catch (_) {
      state = state.copyWith(
        uiState: ProgressUiState.errorRetryable,
        errorCode: 'UNEXPECTED_CLIENT_ERROR',
      );
    }
  }

  void dismissOffer() {
    state = state.copyWith(offerDismissed: true);
  }
}
