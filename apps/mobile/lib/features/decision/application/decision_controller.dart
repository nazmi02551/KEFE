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
    this.responses = const {},
    this.reasonTags = const {},
    this.reasonText = '',
    this.reveal,
    this.errorCode,
  });

  final bool loading;
  final bool submitting;
  final bool recoveryPending;
  final bool offlineDraft;
  final DecisionCase? caseData;
  final String? sessionId;
  final Map<String, Object?> responses;
  final Set<String> reasonTags;
  final String reasonText;
  final RevealResult? reveal;
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
    Map<String, Object?>? responses,
    Set<String>? reasonTags,
    String? reasonText,
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
      responses: responses ?? this.responses,
      reasonTags: reasonTags ?? this.reasonTags,
      reasonText: reasonText ?? this.reasonText,
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

  int _loadGeneration = 0;

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
        state = DecisionState(
          caseData: caseData,
          sessionId: draft.sessionId,
          responses: draft.effectiveResponses,
          reasonTags: draft.reasonTags.toSet(),
          reasonText: draft.reasonText ?? '',
          recoveryPending: draft.phase != DecisionDraftPhase.editing,
        );
        if (draft.phase != DecisionDraftPhase.editing) {
          await _resumeDraft(draft);
        }
        return;
      }

      if (draft != null) {
        await _draftStore.clearForCase(caseId);
      }

      final sessionId = await _repository.startSession(caseData.id);
      if (generation != _loadGeneration) return;
      state = DecisionState(caseData: caseData, sessionId: sessionId);
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
    if (caseData == null || sessionId == null) return;
    if (!caseData.questions.any((question) => question.id == questionId)) return;

    final responses = {...state.responses, questionId: value};
    await _writeEditingDraft(
      caseData: caseData,
      sessionId: sessionId,
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
    final policy = caseData?.reasonPolicy;
    if (caseData == null || sessionId == null || policy == null) return;
    if (!policy.tags.contains(tag)) return;

    final tags = {...state.reasonTags};
    if (!tags.remove(tag)) {
      if (tags.length >= policy.maxTags) return;
      tags.add(tag);
    }
    await _writeEditingDraft(
      caseData: caseData,
      sessionId: sessionId,
      responses: state.responses,
      reasonTags: tags,
      reasonText: state.reasonText,
    );
    state = state.copyWith(reasonTags: tags, offlineDraft: false, clearError: true);
  }

  Future<void> setReasonText(String value) async {
    if (!_inputsEditable) return;
    final caseData = state.caseData;
    final sessionId = state.sessionId;
    final policy = caseData?.reasonPolicy;
    if (caseData == null || sessionId == null || policy == null || !policy.textEnabled) {
      return;
    }

    final text = value.length <= policy.textMaxLength
        ? value
        : value.substring(0, policy.textMaxLength);
    await _writeEditingDraft(
      caseData: caseData,
      sessionId: sessionId,
      responses: state.responses,
      reasonTags: state.reasonTags,
      reasonText: text,
    );
    state = state.copyWith(reasonText: text, offlineDraft: false, clearError: true);
  }

  Future<void> commit() async {
    if (state.submitting || !state.hasRequiredResponses) return;

    final caseData = state.caseData;
    final sessionId = state.sessionId;
    if (caseData == null || sessionId == null) return;

    final stored = await _draftStore.readForCase(caseData.id);
    if (stored != null && stored.phase != DecisionDraftPhase.editing) {
      await _resumeDraft(stored);
      return;
    }

    final pending = DecisionDraft(
      caseData: caseData,
      sessionId: sessionId,
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

  Future<void> _resumeDraft(DecisionDraft draft) async {
    state = state.copyWith(
      submitting: true,
      recoveryPending: true,
      offlineDraft: false,
      clearError: true,
    );

    var current = draft;
    var allowLegacyIncompleteFallback = current.phase == DecisionDraftPhase.commitPending;
    try {
      while (true) {
        if (current.phase == DecisionDraftPhase.syncPending) {
          await _syncDraft(current);
          current = current.copyWith(
            phase: DecisionDraftPhase.commitPending,
            updatedAt: DateTime.now().toUtc(),
          );
          await _draftStore.write(current);
          allowLegacyIncompleteFallback = false;
        }

        if (current.phase == DecisionDraftPhase.commitPending) {
          try {
            await _repository.commit(
              sessionId: current.sessionId,
              idempotencyKey: current.commitIdempotencyKey!,
            );
          } on ApiFailure catch (error) {
            if (allowLegacyIncompleteFallback && error.code == 'WEIGH_RESPONSE_INCOMPLETE') {
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

      final reveal = await _repository.reveal(current.sessionId);
      await _draftStore.clearForCase(current.caseId);
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
        errorCode: switch (current.phase) {
          DecisionDraftPhase.syncPending => 'DECISION_SYNC_PENDING',
          DecisionDraftPhase.commitPending => 'WEIGH_COMMIT_UNCERTAIN',
          DecisionDraftPhase.committedAwaitingReveal => 'RESULT_SYNC_PENDING',
          DecisionDraftPhase.editing => 'NETWORK_UNAVAILABLE',
        },
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

  Future<void> _syncDraft(DecisionDraft draft) async {
    for (final response in draft.effectiveResponses.entries) {
      final value = response.value;
      if (value == null) continue;
      await _repository.answer(
        sessionId: draft.sessionId,
        questionId: response.key,
        value: value,
      );
    }

    final reasonText = _normalizedReasonText(draft.reasonText ?? '');
    if (draft.reasonTags.isNotEmpty || reasonText != null) {
      await _repository.savePrivateReason(
        sessionId: draft.sessionId,
        tags: draft.reasonTags,
        text: reasonText,
      );
    }
  }

  Future<void> _writeEditingDraft({
    required DecisionCase caseData,
    required String sessionId,
    required Map<String, Object?> responses,
    required Set<String> reasonTags,
    required String reasonText,
  }) async {
    await _draftStore.write(
      DecisionDraft(
        caseData: caseData,
        sessionId: sessionId,
        responses: responses,
        reasonTags: reasonTags.toList(growable: false),
        reasonText: _normalizedReasonText(reasonText),
        updatedAt: DateTime.now().toUtc(),
      ),
    );
  }

  void _restoreOfflineDraft(DecisionDraft draft, String transportCode) {
    state = DecisionState(
      caseData: draft.caseData,
      sessionId: draft.sessionId,
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

  bool get _inputsEditable =>
      state.reveal == null && !state.submitting && !state.recoveryPending;

  String? _normalizedReasonText(String value) {
    final normalized = value.trim();
    return normalized.isEmpty ? null : normalized;
  }

  String _idempotencyKey(String sessionId) {
    final random = Random.secure().nextInt(1 << 32).toRadixString(16);
    return 'mobile-$sessionId-$random';
  }
}
