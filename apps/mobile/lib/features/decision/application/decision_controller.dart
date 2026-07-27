import 'dart:math';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;

import '../../../core/config/app_config.dart';
import '../../../core/storage/secure_credential_store.dart';
import '../data/decision_draft_store.dart';
import '../data/decision_repository.dart';
import '../data/http_decision_repository.dart';
import '../domain/decision_draft.dart';
import '../domain/decision_models.dart';

const demoCaseId = '11111111-1111-4111-8111-111111111111';

final appConfigProvider = Provider<AppConfig>((ref) => AppConfig.fromEnvironment());
final httpClientProvider = Provider<http.Client>((ref) {
  final client = http.Client();
  ref.onDispose(client.close);
  return client;
});
final credentialStoreProvider = Provider<CredentialStore>(
  (ref) => SecureCredentialStore(),
);
final decisionDraftStoreProvider = Provider<DecisionDraftStore>(
  (ref) => SharedPreferencesDecisionDraftStore(),
);
final decisionRepositoryProvider = Provider<DecisionRepository>((ref) {
  return HttpDecisionRepository(
    config: ref.watch(appConfigProvider),
    client: ref.watch(httpClientProvider),
    credentialStore: ref.watch(credentialStoreProvider),
  );
});

class DecisionState {
  const DecisionState({
    this.loading = false,
    this.submitting = false,
    this.recoveryPending = false,
    this.offlineDraft = false,
    this.caseData,
    this.sessionId,
    this.selectedOption,
    this.reveal,
    this.errorCode,
  });

  final bool loading;
  final bool submitting;
  final bool recoveryPending;
  final bool offlineDraft;
  final DecisionCase? caseData;
  final String? sessionId;
  final String? selectedOption;
  final RevealResult? reveal;
  final String? errorCode;

  DecisionState copyWith({
    bool? loading,
    bool? submitting,
    bool? recoveryPending,
    bool? offlineDraft,
    DecisionCase? caseData,
    String? sessionId,
    String? selectedOption,
    RevealResult? reveal,
    String? errorCode,
    bool clearError = false,
  }) {
    return DecisionState(
      loading: loading ?? this.loading,
      submitting: submitting ?? this.submitting,
      recoveryPending: recoveryPending ?? this.recoveryPending,
      offlineDraft: offlineDraft ?? this.offlineDraft,
      caseData: caseData ?? this.caseData,
      sessionId: sessionId ?? this.sessionId,
      selectedOption: selectedOption ?? this.selectedOption,
      reveal: reveal ?? this.reveal,
      errorCode: clearError ? null : errorCode ?? this.errorCode,
    );
  }
}

final decisionControllerProvider = NotifierProvider<DecisionController, DecisionState>(
  DecisionController.new,
);

class DecisionController extends Notifier<DecisionState> {
  DecisionRepository get _repository => ref.read(decisionRepositoryProvider);
  DecisionDraftStore get _draftStore => ref.read(decisionDraftStoreProvider);

  @override
  DecisionState build() => const DecisionState();

  Future<void> load() async {
    state = state.copyWith(loading: true, clearError: true);
    final draft = await _draftStore.read();

    try {
      await _repository.ensureGuestCredential();
      final caseData = await _repository.fetchCase(demoCaseId);

      if (draft != null &&
          draft.caseId == caseData.id &&
          draft.caseVersionId == caseData.versionId) {
        state = state.copyWith(
          loading: false,
          caseData: caseData,
          sessionId: draft.sessionId,
          selectedOption: draft.selectedOption,
          recoveryPending: draft.phase != DecisionDraftPhase.editing,
          offlineDraft: false,
          clearError: true,
        );
        if (draft.phase != DecisionDraftPhase.editing) {
          await _resumeDraft(draft);
        }
        return;
      }

      if (draft != null) {
        await _draftStore.clear();
      }

      final sessionId = await _repository.startSession(caseData.id);
      state = state.copyWith(
        loading: false,
        caseData: caseData,
        sessionId: sessionId,
        recoveryPending: false,
        offlineDraft: false,
        clearError: true,
      );
    } on ClientTransportFailure catch (error) {
      if (draft != null) {
        _restoreOfflineDraft(draft, error.code);
        return;
      }
      state = state.copyWith(loading: false, errorCode: error.code);
    } on ApiFailure catch (error) {
      state = state.copyWith(loading: false, errorCode: error.code);
    } catch (_) {
      state = state.copyWith(loading: false, errorCode: 'UNEXPECTED_CLIENT_ERROR');
    }
  }

  Future<void> select(String value) async {
    if (state.reveal != null || state.submitting || state.recoveryPending) return;
    final caseData = state.caseData;
    final sessionId = state.sessionId;
    if (caseData == null || sessionId == null || caseData.questions.isEmpty) return;

    final draft = DecisionDraft(
      caseData: caseData,
      sessionId: sessionId,
      questionId: caseData.questions.first.id,
      selectedOption: value,
      updatedAt: DateTime.now().toUtc(),
    );
    await _draftStore.write(draft);
    state = state.copyWith(
      selectedOption: value,
      offlineDraft: false,
      clearError: true,
    );
  }

  Future<void> commit() async {
    if (state.submitting) return;

    final caseData = state.caseData;
    final sessionId = state.sessionId;
    final selected = state.selectedOption;
    if (caseData == null || sessionId == null || selected == null) return;

    final stored = await _draftStore.read();
    if (stored != null && stored.phase != DecisionDraftPhase.editing) {
      await _resumeDraft(stored);
      return;
    }

    final pending = DecisionDraft(
      caseData: caseData,
      sessionId: sessionId,
      questionId: caseData.questions.first.id,
      selectedOption: selected,
      commitIdempotencyKey:
          stored?.commitIdempotencyKey ?? _idempotencyKey(sessionId),
      phase: DecisionDraftPhase.commitPending,
      updatedAt: DateTime.now().toUtc(),
    );

    try {
      await _draftStore.write(pending);
    } catch (_) {
      state = state.copyWith(errorCode: 'LOCAL_STATE_PERSIST_FAILED');
      return;
    }

    await _resumeDraft(pending);
  }

  Future<void> retryPending() async {
    if (state.submitting) return;
    final draft = await _draftStore.read();
    if (draft == null || draft.phase == DecisionDraftPhase.editing) {
      await commit();
      return;
    }
    await _resumeDraft(draft);
  }

  Future<void> _resumeDraft(DecisionDraft draft) async {
    state = state.copyWith(
      submitting: true,
      recoveryPending: true,
      offlineDraft: false,
      clearError: true,
    );

    var current = draft;
    try {
      if (current.phase == DecisionDraftPhase.commitPending) {
        await _repository.answer(
          sessionId: current.sessionId,
          questionId: current.questionId,
          value: current.selectedOption,
        );
        await _repository.commit(
          sessionId: current.sessionId,
          idempotencyKey: current.commitIdempotencyKey!,
        );
        current = current.copyWith(
          phase: DecisionDraftPhase.committedAwaitingReveal,
          updatedAt: DateTime.now().toUtc(),
        );
        await _draftStore.write(current);
      }

      final reveal = await _repository.reveal(current.sessionId);
      await _draftStore.clear();
      state = state.copyWith(
        submitting: false,
        recoveryPending: false,
        offlineDraft: false,
        reveal: reveal,
        clearError: true,
      );
    } on ClientTransportFailure catch (_) {
      state = state.copyWith(
        submitting: false,
        recoveryPending: true,
        offlineDraft: true,
        errorCode: current.phase == DecisionDraftPhase.commitPending
            ? 'WEIGH_COMMIT_UNCERTAIN'
            : 'RESULT_SYNC_PENDING',
      );
    } on ApiFailure catch (error) {
      state = state.copyWith(
        submitting: false,
        recoveryPending: current.phase != DecisionDraftPhase.editing,
        errorCode: error.code,
      );
    } catch (_) {
      state = state.copyWith(
        submitting: false,
        recoveryPending: true,
        errorCode: 'UNEXPECTED_CLIENT_ERROR',
      );
    }
  }

  void _restoreOfflineDraft(DecisionDraft draft, String transportCode) {
    state = state.copyWith(
      loading: false,
      caseData: draft.caseData,
      sessionId: draft.sessionId,
      selectedOption: draft.selectedOption,
      recoveryPending: draft.phase != DecisionDraftPhase.editing,
      offlineDraft: true,
      errorCode: draft.phase == DecisionDraftPhase.editing
          ? 'OFFLINE_DRAFT_RESTORED'
          : transportCode,
    );
  }

  String _idempotencyKey(String sessionId) {
    final random = Random.secure().nextInt(1 << 32).toRadixString(16);
    return 'mobile-$sessionId-$random';
  }
}
