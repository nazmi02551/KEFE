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

  FlowRuntimeStep? get readyDecisionStep {
    final runtime = flowRuntime;
    if (runtime == null) return null;
    for (final step in runtime.steps) {
      if (step.primitiveCode == 'DECISION' &&
          step.state == FlowStepRuntimeState.ready) {
        return step;
      }
    }
    return null;
  }

  String? get firstDecisionStepCode {
    final runtime = flowRuntime;
    if (runtime == null) return null;
    for (final step in runtime.steps) {
      if (step.primitiveCode == 'DECISION') return step.code;
    }
    return null;
  }

  bool get hasReadyDecisionStep => readyDecisionStep != null;

  DecisionState copyWith({
    bool? loading,
    bool? submitting,
    bool? recoveryPending,
    bool? offlineDraft,
    DecisionCase? caseData,
    String? sessionId,
    FlowRuntimeSnapshot? flowRuntime,
    Map<String, Object?>? responses,
    Set<String>? reasonTags,
    String? reasonText,
    RevealResult? reveal,
    PerspectiveUiState? perspectiveState,
    PerspectiveResult? perspective,
    bool? reasonPendingModeration,
    String? perspectiveErrorCode,
    String? errorCode,
    bool clearPerspectiveError = false,
    bool clearError = false,
  }) {
    return DecisionState(
      loading: loading ?? this.loading,
      submitting: submitting ?? this.submitting,
      recoveryPending: recoveryPending ?? this.recoveryPending,
      offlineDraft: offlineDraft ?? this.offlineDraft,
      caseData: caseData ?? this.caseData,
      sessionId: sessionId ?? this.sessionId,
      flowRuntime: flowRuntime ?? this.flowRuntime,
      responses: responses ?? this.responses,
      reasonTags: reasonTags ?? this.reasonTags,
      reasonText: reasonText ?? this.reasonText,
      reveal: reveal ?? this.reveal,
      perspectiveState: perspectiveState ?? this.perspectiveState,
      perspective: perspective ?? this.perspective,
      reasonPendingModeration:
          reasonPendingModeration ?? this.reasonPendingModeration,
      perspectiveErrorCode: clearPerspectiveError
          ? null
          : perspectiveErrorCode ?? this.perspectiveErrorCode,
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

  int _loadGeneration = 0;
  final Set<String> _exposureInFlight = {};

  @override
  DecisionState build() => const DecisionState();

  Future<void> load(String caseId) async {
    final generation = ++_loadGeneration;
    state = const DecisionState(loading: true);
    final draft = await _draftStore.readForCase(caseId);

    try {
      await _repository.ensureGuestCredential();
      final caseData = await _repository.fetchCase(caseId);
      if (generation != _loadGeneration) return;

      if (draft != null && draft.caseVersionId == caseData.versionId) {
        final flowRuntime = await _repository.fetchFlowRuntime(draft.sessionId);
        _assertFlowMatches(
          flowRuntime,
          sessionId: draft.sessionId,
          caseVersionId: caseData.versionId,
        );
        final flowStepCode = draft.flowStepCode ??
            _readyDecisionStep(flowRuntime)?.code;
        final refreshedDraft = draft.copyWith(
          flowRuntime: flowRuntime,
          flowStepCode: flowStepCode,
          updatedAt: DateTime.now().toUtc(),
        );
        final compatible = draft.phase != DecisionDraftPhase.editing ||
            flowStepCode == null ||
            _stepIsReady(flowRuntime, flowStepCode);
        if (!compatible) {
          await _draftStore.clearForCase(caseId);
          state = DecisionState(
            caseData: caseData,
            sessionId: draft.sessionId,
            flowRuntime: flowRuntime,
          );
          return;
        }
        await _draftStore.write(refreshedDraft);
        state = DecisionState(
          caseData: caseData,
          sessionId: draft.sessionId,
          flowRuntime: flowRuntime,
          responses: draft.effectiveResponses,
          reasonTags: draft.reasonTags.toSet(),
          reasonText: draft.reasonText ?? '',
          recoveryPending: draft.phase != DecisionDraftPhase.editing,
        );
        if (draft.phase != DecisionDraftPhase.editing) {
          await _resumeDraft(refreshedDraft);
        }
        return;
      }

      if (draft != null) {
        await _draftStore.clearForCase(caseId);
      }

      final sessionId = await _repository.startSession(caseData.id);
      if (generation != _loadGeneration) return;
      final flowRuntime = await _repository.fetchFlowRuntime(sessionId);
      _assertFlowMatches(
        flowRuntime,
        sessionId: sessionId,
        caseVersionId: caseData.versionId,
      );
      state = DecisionState(
        caseData: caseData,
        sessionId: sessionId,
        flowRuntime: flowRuntime,
      );
    } on ClientTransportFailure catch (error) {
      if (generation != _loadGeneration) return;
      if (draft != null) {
        _restoreOfflineDraft(draft, error.code);
        return;
      }
      state = DecisionState(errorCode: error.code);
    } on ApiFailure catch (error) {
      if (generation != _loadGeneration) return;
      state = DecisionState(errorCode: error.code);
    } catch (_) {
      if (generation != _loadGeneration) return;
      state = const DecisionState(errorCode: 'UNEXPECTED_CLIENT_ERROR');
    }
  }

  Future<void> select(String value) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    final choice = caseData.questions
        .where((question) => question.responseType == 'SINGLE_CHOICE')
        .firstOrNull;
    if (choice == null) return;
    await setResponse(choice.id, value);
  }

  Future<void> setResponse(String questionId, Object value) async {
    if (!_inputsEditable) return;
    final caseData = state.caseData;
    final sessionId = state.sessionId;
    final stepCode = state.readyDecisionStep?.code;
    if (caseData == null || sessionId == null || stepCode == null) return;
    if (!caseData.questions.any((question) => question.id == questionId)) {
      return;
    }

    final responses = {...state.responses, questionId: value};
    await _writeEditingDraft(
      caseData: caseData,
      sessionId: sessionId,
      flowStepCode: stepCode,
      responses: responses,
      reasonTags: state.reasonTags,
      reasonText: state.reasonText,
    );
    state = state.copyWith(
      responses: responses,
      offlineDraft: false,
      clearError: true,
    );
  }

  Future<void> toggleReasonTag(String tag) async {
    if (!_inputsEditable) return;
    final caseData = state.caseData;
    final sessionId = state.sessionId;
    final stepCode = state.readyDecisionStep?.code;
    final policy = caseData?.reasonPolicy;
    if (caseData == null ||
        sessionId == null ||
        stepCode == null ||
        policy == null) {
      return;
    }
    if (!policy.tags.contains(tag)) return;

    final tags = {...state.reasonTags};
    if (!tags.remove(tag)) {
      if (tags.length >= policy.maxTags) return;
      tags.add(tag);
    }
    await _writeEditingDraft(
      caseData: caseData,
      sessionId: sessionId,
      flowStepCode: stepCode,
      responses: state.responses,
      reasonTags: tags,
      reasonText: state.reasonText,
    );
    state = state.copyWith(
      reasonTags: tags,
      offlineDraft: false,
      clearError: true,
    );
  }

  Future<void> setReasonText(String value) async {
    if (!_inputsEditable) return;
    final caseData = state.caseData;
    final sessionId = state.sessionId;
    final stepCode = state.readyDecisionStep?.code;
    final policy = caseData?.reasonPolicy;
    if (caseData == null ||
        sessionId == null ||
        stepCode == null ||
        policy == null ||
        !policy.textEnabled) {
      return;
    }

    final text = value.length <= policy.textMaxLength
        ? value
        : value.substring(0, policy.textMaxLength);
    await _writeEditingDraft(
      caseData: caseData,
      sessionId: sessionId,
      flowStepCode: stepCode,
      responses: state.responses,
      reasonTags: state.reasonTags,
      reasonText: text,
    );
    state = state.copyWith(
      reasonText: text,
      offlineDraft: false,
      clearError: true,
    );
  }

  Future<void> recordContextExposure(String stepCode) async {
    final sessionId = state.sessionId;
    final caseData = state.caseData;
    final flowRuntime = state.flowRuntime;
    if (sessionId == null || caseData == null || flowRuntime == null) return;
    final step = flowRuntime.steps
        .where((item) => item.code == stepCode && item.primitiveCode == 'CONTEXT')
        .firstOrNull;
    if (step == null || step.state != FlowStepRuntimeState.ready) return;

    final marker = '$sessionId:$stepCode';
    if (!_exposureInFlight.add(marker)) return;
    final beforeReady = state.readyDecisionStep?.code;
    try {
      await _repository.lineage.recordFlowStepExposure(
        sessionId: sessionId,
        stepCode: stepCode,
        idempotencyKey: 'mobile-flow-exposure-$sessionId-$stepCode-v1',
      );
      final refreshed = await _repository.fetchFlowRuntime(sessionId);
      _assertFlowMatches(
        refreshed,
        sessionId: sessionId,
        caseVersionId: caseData.versionId,
      );
      final afterReady = _readyDecisionStep(refreshed)?.code;
      final enteredNewDecision = afterReady != null && afterReady != beforeReady;
      if (enteredNewDecision) {
        await _draftStore.clearForCase(caseData.id);
      }
      state = state.copyWith(
        flowRuntime: refreshed,
        responses: enteredNewDecision ? const {} : state.responses,
        reasonTags: enteredNewDecision ? const {} : state.reasonTags,
        reasonText: enteredNewDecision ? '' : state.reasonText,
        recoveryPending: false,
        offlineDraft: false,
        clearError: true,
      );
    } on ClientTransportFailure catch (error) {
      _exposureInFlight.remove(marker);
      state = state.copyWith(
        offlineDraft: true,
        errorCode: error.code,
      );
    } on ApiFailure catch (error) {
      _exposureInFlight.remove(marker);
      state = state.copyWith(errorCode: error.code);
    } catch (_) {
      _exposureInFlight.remove(marker);
      state = state.copyWith(errorCode: 'UNEXPECTED_CLIENT_ERROR');
    }
  }

  Future<void> commit() async {
    final readyStep = state.readyDecisionStep;
    if (state.submitting ||
        !state.hasRequiredResponses ||
        readyStep == null) {
      return;
    }

    final caseData = state.caseData;
    final sessionId = state.sessionId;
    final flowRuntime = state.flowRuntime;
    if (caseData == null || sessionId == null || flowRuntime == null) return;

    final stored = await _draftStore.readForCase(caseData.id);
    if (stored != null && stored.phase != DecisionDraftPhase.editing) {
      await _resumeDraft(stored);
      return;
    }

    final pending = DecisionDraft(
      caseData: caseData,
      sessionId: sessionId,
      flowRuntime: flowRuntime,
      flowStepCode: readyStep.code,
      responses: state.responses,
      reasonTags: state.reasonTags.toList(growable: false),
      reasonText: _normalizedReasonText(state.reasonText),
      commitIdempotencyKey:
          stored?.commitIdempotencyKey ?? _idempotencyKey(sessionId),
      phase: DecisionDraftPhase.syncPending,
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
    final caseData = state.caseData;
    if (caseData == null) return;

    final draft = await _draftStore.readForCase(caseData.id);
    if (draft == null || draft.phase == DecisionDraftPhase.editing) {
      await commit();
      return;
    }
    await _resumeDraft(draft);
  }

  Future<void> retryPerspective() async {
    final sessionId = state.sessionId;
    if (state.reveal == null || sessionId == null) return;
    await _loadPerspective(sessionId);
  }

  Future<void> _resumeDraft(DecisionDraft draft) async {
    state = state.copyWith(
      submitting: true,
      recoveryPending: true,
      offlineDraft: false,
      flowRuntime: draft.flowRuntime,
      clearError: true,
    );

    var current = draft;
    final stepCode = _resolveDraftStep(current);
    if (stepCode == null) {
      state = state.copyWith(
        submitting: false,
        recoveryPending: false,
        errorCode: 'FLOW_DECISION_STEP_UNAVAILABLE',
      );
      return;
    }
    current = current.copyWith(flowStepCode: stepCode);
    final revision = _isRevisionStep(current.flowRuntime, stepCode);
    var allowLegacyIncompleteFallback =
        !revision && current.phase == DecisionDraftPhase.commitPending;
    try {
      while (true) {
        if (current.phase == DecisionDraftPhase.syncPending) {
          await _syncDraft(current, revision: revision);
          current = current.copyWith(
            phase: DecisionDraftPhase.commitPending,
            updatedAt: DateTime.now().toUtc(),
          );
          await _draftStore.write(current);
          allowLegacyIncompleteFallback = false;
        }

        if (current.phase == DecisionDraftPhase.commitPending) {
          try {
            if (revision) {
              await _repository.lineage.commitRevision(
                sessionId: current.sessionId,
                stepCode: stepCode,
                idempotencyKey: current.commitIdempotencyKey!,
              );
            } else {
              await _repository.commit(
                sessionId: current.sessionId,
                idempotencyKey: current.commitIdempotencyKey!,
              );
            }
          } on ApiFailure catch (error) {
            if (allowLegacyIncompleteFallback &&
                error.code == 'WEIGH_RESPONSE_INCOMPLETE') {
              current = current.copyWith(
                phase: DecisionDraftPhase.syncPending,
                updatedAt: DateTime.now().toUtc(),
              );
              await _draftStore.write(current);
              allowLegacyIncompleteFallback = false;
              continue;
            }
            rethrow;
          }
          current = current.copyWith(
            phase: DecisionDraftPhase.committedAwaitingReveal,
            updatedAt: DateTime.now().toUtc(),
          );
          await _draftStore.write(current);
        }
        break;
      }

      final flowRuntime = await _repository.fetchFlowRuntime(current.sessionId);
      _assertFlowMatches(
        flowRuntime,
        sessionId: current.sessionId,
        caseVersionId: current.caseVersionId,
      );
      final resultReady = flowRuntime.steps.any(
        (step) =>
            step.primitiveCode == 'COLLECTIVE_RESULT' &&
            step.state == FlowStepRuntimeState.ready,
      );

      if (!resultReady) {
        await _draftStore.clearForCase(current.caseId);
        state = state.copyWith(
          submitting: false,
          recoveryPending: false,
          offlineDraft: false,
          flowRuntime: flowRuntime,
          responses: const {},
          reasonTags: const {},
          reasonText: '',
          reasonPendingModeration: false,
          clearPerspectiveError: true,
          clearError: true,
        );
        return;
      }

      final reveal = await _repository.reveal(current.sessionId);
      await _draftStore.clearForCase(current.caseId);
      state = state.copyWith(
        submitting: false,
        recoveryPending: false,
        offlineDraft: false,
        flowRuntime: flowRuntime,
        reveal: reveal,
        reasonPendingModeration:
            _normalizedReasonText(current.reasonText ?? '') != null,
        perspectiveState: PerspectiveUiState.loading,
        clearPerspectiveError: true,
        clearError: true,
      );
      await _loadPerspective(current.sessionId, alreadyLoading: true);
    } on ClientTransportFailure catch (_) {
      state = state.copyWith(
        submitting: false,
        recoveryPending: true,
        offlineDraft: true,
        flowRuntime: current.flowRuntime,
        errorCode: switch (current.phase) {
          DecisionDraftPhase.syncPending => 'DECISION_SYNC_PENDING',
          DecisionDraftPhase.commitPending => revision
              ? 'DECISION_REVISION_COMMIT_UNCERTAIN'
              : 'WEIGH_COMMIT_UNCERTAIN',
          DecisionDraftPhase.committedAwaitingReveal => revision
              ? 'FLOW_CONTINUATION_PENDING'
              : 'RESULT_SYNC_PENDING',
          DecisionDraftPhase.editing => 'NETWORK_UNAVAILABLE',
        },
      );
    } on ApiFailure catch (error) {
      state = state.copyWith(
        submitting: false,
        recoveryPending: current.phase != DecisionDraftPhase.editing,
        flowRuntime: current.flowRuntime,
        errorCode: error.code,
      );
    } catch (_) {
      state = state.copyWith(
        submitting: false,
        recoveryPending: true,
        flowRuntime: current.flowRuntime,
        errorCode: 'UNEXPECTED_CLIENT_ERROR',
      );
    }
  }

  Future<void> _loadPerspective(
    String sessionId, {
    bool alreadyLoading = false,
  }) async {
    if (!alreadyLoading) {
      state = state.copyWith(
        perspectiveState: PerspectiveUiState.loading,
        clearPerspectiveError: true,
      );
    }
    try {
      final result = await _repository.fetchPerspectives(sessionId);
      final caseVersionId = state.caseData?.versionId;
      if (result.sessionId != sessionId ||
          caseVersionId == null ||
          result.caseVersionId != caseVersionId) {
        state = state.copyWith(
          perspectiveState: PerspectiveUiState.errorRetryable,
          perspectiveErrorCode: 'PERSPECTIVE_VERSION_MISMATCH',
        );
        return;
      }
      state = state.copyWith(
        perspectiveState: result.uiState,
        perspective: result,
        clearPerspectiveError: true,
      );
    } on ClientTransportFailure catch (error) {
      state = state.copyWith(
        perspectiveState: PerspectiveUiState.errorRetryable,
        perspectiveErrorCode: error.code,
      );
    } on ApiFailure catch (error) {
      state = state.copyWith(
        perspectiveState: PerspectiveUiState.errorRetryable,
        perspectiveErrorCode: error.code,
      );
    } catch (_) {
      state = state.copyWith(
        perspectiveState: PerspectiveUiState.errorRetryable,
        perspectiveErrorCode: 'UNEXPECTED_PERSPECTIVE_ERROR',
      );
    }
  }

  Future<void> _syncDraft(
    DecisionDraft draft, {
    required bool revision,
  }) async {
    final stepCode = draft.flowStepCode;
    if (stepCode == null) {
      throw const ClientTransportFailure(code: 'FLOW_DECISION_STEP_UNAVAILABLE');
    }
    for (final response in draft.effectiveResponses.entries) {
      final value = response.value;
      if (value == null) continue;
      if (revision) {
        await _repository.lineage.answerRevision(
          sessionId: draft.sessionId,
          stepCode: stepCode,
          questionId: response.key,
          value: value,
        );
      } else {
        await _repository.answer(
          sessionId: draft.sessionId,
          questionId: response.key,
          value: value,
        );
      }
    }

    final reasonText = _normalizedReasonText(draft.reasonText ?? '');
    if (draft.reasonTags.isNotEmpty || reasonText != null) {
      if (revision) {
        await _repository.lineage.saveRevisionReason(
          sessionId: draft.sessionId,
          stepCode: stepCode,
          tags: draft.reasonTags,
          text: reasonText,
        );
      } else {
        await _repository.savePrivateReason(
          sessionId: draft.sessionId,
          tags: draft.reasonTags,
          text: reasonText,
        );
      }
    }
  }

  Future<void> _writeEditingDraft({
    required DecisionCase caseData,
    required String sessionId,
    required String flowStepCode,
    required Map<String, Object?> responses,
    required Set<String> reasonTags,
    required String reasonText,
  }) async {
    final flowRuntime = state.flowRuntime;
    if (flowRuntime == null) return;
    await _draftStore.write(
      DecisionDraft(
        caseData: caseData,
        sessionId: sessionId,
        flowRuntime: flowRuntime,
        flowStepCode: flowStepCode,
        responses: responses,
        reasonTags: reasonTags.toList(growable: false),
        reasonText: _normalizedReasonText(reasonText),
        updatedAt: DateTime.now().toUtc(),
      ),
    );
  }

  void _restoreOfflineDraft(DecisionDraft draft, String transportCode) {
    final flowRuntime = draft.flowRuntime;
    if (flowRuntime == null ||
        !flowRuntime.matches(
          sessionId: draft.sessionId,
          caseVersionId: draft.caseVersionId,
        )) {
      state = DecisionState(
        caseData: draft.caseData,
        sessionId: draft.sessionId,
        responses: draft.effectiveResponses,
        reasonTags: draft.reasonTags.toSet(),
        reasonText: draft.reasonText ?? '',
        recoveryPending: draft.phase != DecisionDraftPhase.editing,
        offlineDraft: true,
        errorCode: 'FLOW_RUNTIME_OFFLINE_UNAVAILABLE',
      );
      return;
    }

    state = DecisionState(
      caseData: draft.caseData,
      sessionId: draft.sessionId,
      flowRuntime: flowRuntime,
      responses: draft.effectiveResponses,
      reasonTags: draft.reasonTags.toSet(),
      reasonText: draft.reasonText ?? '',
      recoveryPending: draft.phase != DecisionDraftPhase.editing,
      offlineDraft: true,
      errorCode: draft.phase == DecisionDraftPhase.editing
          ? 'OFFLINE_DRAFT_RESTORED'
          : transportCode,
    );
  }

  void _assertFlowMatches(
    FlowRuntimeSnapshot flowRuntime, {
    required String sessionId,
    required String caseVersionId,
  }) {
    if (!flowRuntime.matches(
      sessionId: sessionId,
      caseVersionId: caseVersionId,
    )) {
      throw ApiFailure('FLOW_RUNTIME_VERSION_MISMATCH', 409);
    }
  }

  FlowRuntimeStep? _readyDecisionStep(FlowRuntimeSnapshot flowRuntime) {
    for (final step in flowRuntime.steps) {
      if (step.primitiveCode == 'DECISION' &&
          step.state == FlowStepRuntimeState.ready) {
        return step;
      }
    }
    return null;
  }

  bool _stepIsReady(FlowRuntimeSnapshot flowRuntime, String stepCode) {
    return flowRuntime.steps.any(
      (step) =>
          step.code == stepCode &&
          step.primitiveCode == 'DECISION' &&
          step.state == FlowStepRuntimeState.ready,
    );
  }

  String? _resolveDraftStep(DecisionDraft draft) {
    final explicit = draft.flowStepCode;
    if (explicit != null) return explicit;
    final runtime = draft.flowRuntime;
    if (runtime == null) return null;
    return _readyDecisionStep(runtime)?.code;
  }

  bool _isRevisionStep(FlowRuntimeSnapshot? runtime, String stepCode) {
    if (runtime == null) return false;
    String? firstDecision;
    for (final step in runtime.steps) {
      if (step.primitiveCode == 'DECISION') {
        firstDecision = step.code;
        break;
      }
    }
    return firstDecision != null && stepCode != firstDecision;
  }

  bool get _inputsEditable =>
      !state.submitting &&
      !state.recoveryPending &&
      state.readyDecisionStep != null;

  String? _normalizedReasonText(String value) {
    final normalized = value.trim();
    return normalized.isEmpty ? null : normalized;
  }

  String _idempotencyKey(String sessionId) {
    final random = Random.secure().nextInt(1 << 32).toRadixString(16);
    return 'mobile-$sessionId-$random';
  }
}
