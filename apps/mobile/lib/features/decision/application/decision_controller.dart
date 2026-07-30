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
  (ref) => SecureDecisionDraftStore(),
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
    this.flowRuntime,
    this.responses = const {},
    this.reasonTags = const {},
    this.reasonText = '',
    this.reveal,
    this.perspectiveState = PerspectiveUiState.idle,
    this.perspective,
    this.reasonPendingModeration = false,
    this.perspectiveErrorCode,
    this.errorCode,
  });

  final bool loading;
  final bool submitting;
  final bool recoveryPending;
  final bool offlineDraft;
  final DecisionCase? caseData;
  final String? sessionId;
  final FlowRuntimeSnapshot? flowRuntime;
  final Map<String, Object?> responses;
  final Set<String> reasonTags;
  final String reasonText;
  final RevealResult? reveal;
  final PerspectiveUiState perspectiveState;
  final PerspectiveResult? perspective;
  final bool reasonPendingModeration;
  final String? perspectiveErrorCode;
  final String? errorCode;

  Object? responseFor(String questionId) => responses[questionId];

  String? get selectedOption {
    final caseValue = caseData;
    if (caseValue == null) return null;
    for (final question in caseValue.questions) {
      if (question.responseType == 'SINGLE_CHOICE') {
        return responses[question.id] as String?;
      }
    }
    return null;
  }

  bool get hasRequiredResponses {
    final caseValue = caseData;
    if (caseValue == null) return false;
    return caseValue.questions
        .where((question) => question.required)
        .every((question) => responses.containsKey(question.id));
  }

  DecisionState copyWith({
    bool? loading,
    bool? submitting,
    bool? recoveryPending,
    bool? offlineDraft,
    DecisionCase? caseData,
    String? sessionId,
    FlowRuntimeSnapshot? flowRuntime,
    bool clearFlowRuntime = false,
    Map<String, Object?>? responses,
    Set<String>? reasonTags,
    String? reasonText,
    RevealResult? reveal,
    bool clearReveal = false,
    PerspectiveUiState? perspectiveState,
    PerspectiveResult? perspective,
    bool clearPerspective = false,
    bool? reasonPendingModeration,
    String? perspectiveErrorCode,
    bool clearPerspectiveError = false,
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
      flowRuntime: clearFlowRuntime ? null : flowRuntime ?? this.flowRuntime,
      responses: responses ?? this.responses,
      reasonTags: reasonTags ?? this.reasonTags,
      reasonText: reasonText ?? this.reasonText,
      reveal: clearReveal ? null : reveal ?? this.reveal,
      perspectiveState: perspectiveState ?? this.perspectiveState,
      perspective: clearPerspective ? null : perspective ?? this.perspective,
      reasonPendingModeration:
          reasonPendingModeration ?? this.reasonPendingModeration,
      perspectiveErrorCode: clearPerspectiveError
          ? null
          : perspectiveErrorCode ?? this.perspectiveErrorCode,
      errorCode: clearError ? null : errorCode ?? this.errorCode,
    );
  }
}

enum PerspectiveUiState {
  idle,
  loading,
  ready,
  errorRetryable,
}

final decisionControllerProvider =
    NotifierProvider<DecisionController, DecisionState>(DecisionController.new);

class DecisionController extends Notifier<DecisionState> {
  DecisionRepository get _repository => ref.read(decisionRepositoryProvider);
  DecisionDraftStore get _draftStore => ref.read(decisionDraftStoreProvider);
  String? _commitKey;
  final Map<String, String> _revisionCommitKeys = {};

  @override
  DecisionState build() => const DecisionState();

  Future<void> loadCase(String caseId) async {
    state = const DecisionState(loading: true);
    try {
      final existingDraft = await _draftStore.readForCase(caseId);
      if (existingDraft != null) {
        await _restoreDraft(existingDraft);
        return;
      }

      final caseData = await _repository.fetchCase(caseId);
      final sessionId = await _repository.startSession(caseId);
      final flowRuntime = await _repository.fetchFlowRuntime(sessionId);
      state = DecisionState(
        caseData: caseData,
        sessionId: sessionId,
        flowRuntime: flowRuntime,
      );
      await _persistDraft(DecisionDraftPhase.editing);
    } on ClientTransportFailure catch (_) {
      final existingDraft = await _draftStore.readForCase(caseId);
      if (existingDraft != null) {
        await _restoreDraft(existingDraft, offline: true);
        return;
      }
      state = const DecisionState(errorCode: 'NETWORK_UNAVAILABLE');
    } on ApiFailure catch (error) {
      state = DecisionState(errorCode: error.code);
    } catch (_) {
      state = const DecisionState(errorCode: 'UNEXPECTED_CLIENT_ERROR');
    }
  }

  Future<void> _restoreDraft(
    DecisionDraft draft, {
    bool offline = false,
  }) async {
    _commitKey = draft.commitIdempotencyKey;
    state = DecisionState(
      caseData: draft.caseData,
      sessionId: draft.sessionId,
      flowRuntime: draft.flowRuntime,
      responses: draft.effectiveResponses,
      reasonTags: draft.reasonTags.toSet(),
      reasonText: draft.reasonText ?? '',
      offlineDraft: offline || draft.phase == DecisionDraftPhase.syncPending,
      recoveryPending: draft.phase == DecisionDraftPhase.commitPending,
    );
    if (draft.phase == DecisionDraftPhase.commitPending) {
      await _recoverCommit();
    } else if (draft.phase == DecisionDraftPhase.committedAwaitingReveal) {
      await _loadReveal();
    }
  }

  void selectResponse(String questionId, Object? value) {
    final caseValue = state.caseData;
    final question = caseValue?.questions
        .where((item) => item.id == questionId)
        .firstOrNull;
    if (question == null) return;
    final next = {...state.responses, questionId: value};
    state = state.copyWith(
      responses: next,
      clearReveal: true,
      perspectiveState: PerspectiveUiState.idle,
      clearPerspective: true,
      clearPerspectiveError: true,
      clearError: true,
    );
    _persistDraft(DecisionDraftPhase.editing);
  }

  void selectOption(String option) {
    final caseValue = state.caseData;
    if (caseValue == null) return;
    final question = caseValue.questions.firstWhere(
      (item) => item.responseType == 'SINGLE_CHOICE',
      orElse: () => caseValue.questions.first,
    );
    selectResponse(question.id, option);
  }

  void toggleReasonTag(String tag) {
    final next = {...state.reasonTags};
    if (!next.remove(tag)) next.add(tag);
    state = state.copyWith(reasonTags: next, clearError: true);
    _persistDraft(DecisionDraftPhase.editing);
  }

  void setReasonText(String value) {
    state = state.copyWith(reasonText: value, clearError: true);
    _persistDraft(DecisionDraftPhase.editing);
  }

  Future<void> commit() async {
    if (!state.hasRequiredResponses || state.submitting) return;
    final sessionId = state.sessionId;
    if (sessionId == null) return;

    _commitKey ??= _newIdempotencyKey('commit');
    state = state.copyWith(submitting: true, clearError: true);
    await _persistDraft(DecisionDraftPhase.commitPending);

    try {
      await _syncDraft(sessionId);
      await _repository.commit(sessionId, _commitKey!);
      state = state.copyWith(
        submitting: false,
        recoveryPending: false,
        offlineDraft: false,
      );
      await _persistDraft(DecisionDraftPhase.committedAwaitingReveal);
      await _loadReveal();
    } on ApiFailure catch (error) {
      if (error.code == 'WEIGH_SESSION_ALREADY_COMMITTED') {
        await _loadReveal();
        return;
      }
      state = state.copyWith(submitting: false, errorCode: error.code);
    } on ClientTransportFailure catch (_) {
      state = state.copyWith(
        submitting: false,
        recoveryPending: true,
        errorCode: 'COMMIT_STATUS_UNKNOWN',
      );
      await _persistDraft(DecisionDraftPhase.commitPending);
    } catch (_) {
      state = state.copyWith(
        submitting: false,
        recoveryPending: true,
        errorCode: 'COMMIT_STATUS_UNKNOWN',
      );
      await _persistDraft(DecisionDraftPhase.commitPending);
    }
  }

  Future<void> retryRecovery() async => _recoverCommit();

  Future<void> _recoverCommit() async {
    final sessionId = state.sessionId;
    final key = _commitKey;
    if (sessionId == null || key == null) return;
    state = state.copyWith(submitting: true, recoveryPending: true);
    try {
      await _repository.commit(sessionId, key);
      state = state.copyWith(
        submitting: false,
        recoveryPending: false,
        offlineDraft: false,
        clearError: true,
      );
      await _persistDraft(DecisionDraftPhase.committedAwaitingReveal);
      await _loadReveal();
    } on ApiFailure catch (error) {
      if (error.code == 'WEIGH_SESSION_ALREADY_COMMITTED') {
        await _loadReveal();
        return;
      }
      state = state.copyWith(submitting: false, errorCode: error.code);
    } on ClientTransportFailure catch (_) {
      state = state.copyWith(
        submitting: false,
        recoveryPending: true,
        errorCode: 'COMMIT_STATUS_UNKNOWN',
      );
    }
  }

  Future<void> _syncDraft(String sessionId) async {
    try {
      await _repository.updateResponses(sessionId, state.responses);
      if (state.reasonTags.isNotEmpty || state.reasonText.trim().isNotEmpty) {
        final reason = await _repository.updatePrivateReason(
          sessionId,
          state.reasonTags.toList(growable: false),
          state.reasonText.trim().isEmpty ? null : state.reasonText.trim(),
        );
        state = state.copyWith(
          reasonPendingModeration: reason.moderationState == 'PENDING',
        );
      }
    } on ClientTransportFailure {
      await _persistDraft(DecisionDraftPhase.syncPending);
      rethrow;
    }
  }

  Future<void> _loadReveal() async {
    final sessionId = state.sessionId;
    if (sessionId == null) return;
    try {
      final reveal = await _repository.fetchReveal(sessionId);
      state = state.copyWith(
        reveal: reveal,
        submitting: false,
        recoveryPending: false,
        offlineDraft: false,
        clearError: true,
      );
      await _draftStore.clearForCase(state.caseData!.id);
      await loadPerspectives();
    } on ApiFailure catch (error) {
      state = state.copyWith(
        submitting: false,
        recoveryPending: false,
        errorCode: error.code,
      );
    } on ClientTransportFailure catch (_) {
      state = state.copyWith(
        submitting: false,
        recoveryPending: false,
        errorCode: 'REVEAL_UNAVAILABLE',
      );
    }
  }

  Future<void> loadPerspectives() async {
    final sessionId = state.sessionId;
    if (sessionId == null || state.reveal == null) return;
    state = state.copyWith(
      perspectiveState: PerspectiveUiState.loading,
      clearPerspectiveError: true,
    );
    try {
      final result = await _repository.fetchPerspectives(sessionId);
      state = state.copyWith(
        perspectiveState: PerspectiveUiState.ready,
        perspective: result,
        clearPerspectiveError: true,
      );
    } on ApiFailure catch (error) {
      state = state.copyWith(
        perspectiveState: PerspectiveUiState.errorRetryable,
        perspectiveErrorCode: error.code,
      );
    } on ClientTransportFailure catch (error) {
      state = state.copyWith(
        perspectiveState: PerspectiveUiState.errorRetryable,
        perspectiveErrorCode: error.code,
      );
    } catch (_) {
      state = state.copyWith(
        perspectiveState: PerspectiveUiState.errorRetryable,
        perspectiveErrorCode: 'PERSPECTIVE_UNEXPECTED_CLIENT_ERROR',
      );
    }
  }

  Future<void> retryPerspectives() => loadPerspectives();

  Future<void> updateRevisionDraft({
    required String flowStepCode,
    required String questionId,
    required Object? value,
  }) async {
    final sessionId = state.sessionId;
    if (sessionId == null) return;
    try {
      await _repository.updateRevisionDraft(
        sessionId: sessionId,
        flowStepCode: flowStepCode,
        responses: {questionId: value},
      );
    } on ApiFailure catch (error) {
      state = state.copyWith(errorCode: error.code);
    } on ClientTransportFailure catch (error) {
      state = state.copyWith(errorCode: error.code);
    }
  }

  Future<void> commitRevision(String flowStepCode) async {
    final sessionId = state.sessionId;
    if (sessionId == null) return;
    final key = _revisionCommitKeys.putIfAbsent(
      flowStepCode,
      () => _newIdempotencyKey('revision'),
    );
    try {
      await _repository.commitRevision(
        sessionId: sessionId,
        flowStepCode: flowStepCode,
        idempotencyKey: key,
      );
      _revisionCommitKeys.remove(flowStepCode);
    } on ApiFailure catch (error) {
      state = state.copyWith(errorCode: error.code);
    } on ClientTransportFailure catch (error) {
      state = state.copyWith(errorCode: error.code);
    }
  }

  Future<void> completeReflection(String flowStepCode) async {
    final sessionId = state.sessionId;
    if (sessionId == null) return;
    try {
      await _repository.completeReflection(
        sessionId: sessionId,
        flowStepCode: flowStepCode,
        idempotencyKey: _newIdempotencyKey('reflection'),
      );
    } on ApiFailure catch (error) {
      state = state.copyWith(errorCode: error.code);
    } on ClientTransportFailure catch (error) {
      state = state.copyWith(errorCode: error.code);
    }
  }

  Future<void> _persistDraft(DecisionDraftPhase phase) async {
    final caseData = state.caseData;
    final sessionId = state.sessionId;
    if (caseData == null || sessionId == null) return;
    await _draftStore.write(
      DecisionDraft(
        caseData: caseData,
        sessionId: sessionId,
        flowRuntime: state.flowRuntime,
        responses: state.responses,
        reasonTags: state.reasonTags.toList(growable: false),
        reasonText: state.reasonText.trim().isEmpty ? null : state.reasonText.trim(),
        commitIdempotencyKey: _commitKey,
        phase: phase,
        updatedAt: DateTime.now().toUtc(),
      ),
    );
  }

  String _newIdempotencyKey(String prefix) {
    final random = Random.secure();
    return '$prefix-${DateTime.now().microsecondsSinceEpoch}-${random.nextInt(1 << 32)}';
  }
}
