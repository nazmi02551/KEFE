import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../decision/application/decision_controller.dart';
import '../../decision/data/decision_repository.dart';
import '../../decision/data/http_decision_repository.dart';
import '../data/http_share_repository.dart';
import '../data/share_repository.dart';

final shareExperienceEnabledProvider = Provider<bool>((ref) => false);

final shareRepositoryProvider = Provider<ShareRepository>((ref) {
  if (!ref.watch(shareExperienceEnabledProvider)) {
    return const _DisabledShareRepository();
  }
  return HttpShareRepository(
    config: ref.watch(appConfigProvider),
    client: ref.watch(httpClientProvider),
    credentialStore: ref.watch(credentialStoreProvider),
  );
});

enum ShareUiState { idle, creating, ready, error }

class ShareState {
  const ShareState({this.uiState = ShareUiState.idle, this.created, this.errorCode});

  final ShareUiState uiState;
  final CreatedShare? created;
  final String? errorCode;

  ShareState copyWith({
    ShareUiState? uiState,
    CreatedShare? created,
    String? errorCode,
    bool clearError = false,
  }) => ShareState(
    uiState: uiState ?? this.uiState,
    created: created ?? this.created,
    errorCode: clearError ? null : errorCode ?? this.errorCode,
  );
}

final shareControllerProvider = NotifierProvider<ShareController, ShareState>(
  ShareController.new,
);

class ShareController extends Notifier<ShareState> {
  ShareRepository get _repository => ref.read(shareRepositoryProvider);

  @override
  ShareState build() => const ShareState();

  Future<void> create(String sessionId) async {
    if (state.uiState == ShareUiState.creating) return;
    state = state.copyWith(uiState: ShareUiState.creating, clearError: true);
    try {
      final created = await _repository.create(
        sessionId: sessionId,
        includeDecision: false,
      );
      state = state.copyWith(
        uiState: ShareUiState.ready,
        created: created,
        clearError: true,
      );
    } on ApiFailure catch (error) {
      state = state.copyWith(
        uiState: ShareUiState.error,
        errorCode: error.code,
      );
    } on ClientTransportFailure catch (error) {
      state = state.copyWith(
        uiState: ShareUiState.error,
        errorCode: error.code,
      );
    }
  }

  Future<void> revoke() async {
    final created = state.created;
    if (created == null) return;
    try {
      await _repository.revoke(created.id);
      state = const ShareState();
    } on ApiFailure catch (error) {
      state = state.copyWith(
        uiState: ShareUiState.error,
        errorCode: error.code,
      );
    } on ClientTransportFailure catch (error) {
      state = state.copyWith(
        uiState: ShareUiState.error,
        errorCode: error.code,
      );
    }
  }
}

class _DisabledShareRepository implements ShareRepository {
  const _DisabledShareRepository();

  @override
  Future<CreatedShare> create({
    required String sessionId,
    required bool includeDecision,
  }) => throw const ClientTransportFailure(code: 'SHARE_NOT_ENABLED');

  @override
  Future<PublicShare> read(String token) =>
      throw const ClientTransportFailure(code: 'SHARE_NOT_ENABLED');

  @override
  Future<void> revoke(String shareId) =>
      throw const ClientTransportFailure(code: 'SHARE_NOT_ENABLED');
}
