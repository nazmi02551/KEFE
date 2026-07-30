import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../decision/application/decision_controller.dart';
import '../../decision/data/decision_repository.dart';
import '../../decision/data/http_decision_repository.dart';
import '../data/http_privacy_repository.dart';
import '../data/privacy_repository.dart';

final privacyExperienceEnabledProvider = Provider<bool>((ref) => false);

final privacyRepositoryProvider = Provider<PrivacyRepository>((ref) {
  if (!ref.watch(privacyExperienceEnabledProvider)) {
    return const _DisabledPrivacyRepository();
  }
  return HttpPrivacyRepository(
    config: ref.watch(appConfigProvider),
    client: ref.watch(httpClientProvider),
    credentialStore: ref.watch(credentialStoreProvider),
  );
});

enum PrivacyUiState { idle, working, deleted, error }

class PrivacyState {
  const PrivacyState({
    this.uiState = PrivacyUiState.idle,
    this.lastExport,
    this.deletion,
    this.errorCode,
  });

  final PrivacyUiState uiState;
  final Map<String, Object?>? lastExport;
  final PrivacyDeletionReceipt? deletion;
  final String? errorCode;

  PrivacyState copyWith({
    PrivacyUiState? uiState,
    Map<String, Object?>? lastExport,
    PrivacyDeletionReceipt? deletion,
    String? errorCode,
    bool clearError = false,
  }) => PrivacyState(
    uiState: uiState ?? this.uiState,
    lastExport: lastExport ?? this.lastExport,
    deletion: deletion ?? this.deletion,
    errorCode: clearError ? null : errorCode ?? this.errorCode,
  );
}

final privacyControllerProvider =
    NotifierProvider<PrivacyController, PrivacyState>(PrivacyController.new);

class PrivacyController extends Notifier<PrivacyState> {
  PrivacyRepository get _repository => ref.read(privacyRepositoryProvider);

  @override
  PrivacyState build() => const PrivacyState();

  Future<Map<String, Object?>?> export() async {
    state = state.copyWith(uiState: PrivacyUiState.working, clearError: true);
    try {
      final data = await _repository.export();
      state = state.copyWith(
        uiState: PrivacyUiState.idle,
        lastExport: data,
        clearError: true,
      );
      return data;
    } on ApiFailure catch (error) {
      state = state.copyWith(
        uiState: PrivacyUiState.error,
        errorCode: error.code,
      );
    } on ClientTransportFailure catch (error) {
      state = state.copyWith(
        uiState: PrivacyUiState.error,
        errorCode: error.code,
      );
    }
    return null;
  }

  Future<bool> delete() async {
    state = state.copyWith(uiState: PrivacyUiState.working, clearError: true);
    try {
      final receipt = await _repository.delete();
      state = state.copyWith(
        uiState: PrivacyUiState.deleted,
        deletion: receipt,
        clearError: true,
      );
      return true;
    } on ApiFailure catch (error) {
      state = state.copyWith(
        uiState: PrivacyUiState.error,
        errorCode: error.code,
      );
    } on ClientTransportFailure catch (error) {
      state = state.copyWith(
        uiState: PrivacyUiState.error,
        errorCode: error.code,
      );
    }
    return false;
  }
}

class _DisabledPrivacyRepository implements PrivacyRepository {
  const _DisabledPrivacyRepository();

  @override
  Future<Map<String, Object?>> export() =>
      throw const ClientTransportFailure(code: 'PRIVACY_NOT_ENABLED');

  @override
  Future<PrivacyDeletionReceipt> delete() =>
      throw const ClientTransportFailure(code: 'PRIVACY_NOT_ENABLED');
}
