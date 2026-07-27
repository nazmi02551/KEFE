import 'dart:math';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;

import '../../../core/config/app_config.dart';
import '../data/decision_repository.dart';
import '../data/http_decision_repository.dart';
import '../domain/decision_models.dart';

const demoCaseId = '11111111-1111-4111-8111-111111111111';

final appConfigProvider = Provider<AppConfig>((ref) => AppConfig.fromEnvironment());
final httpClientProvider = Provider<http.Client>((ref) {
  final client = http.Client();
  ref.onDispose(client.close);
  return client;
});
final credentialStoreProvider = Provider<CredentialStore>((ref) => MemoryCredentialStore());
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
    this.caseData,
    this.sessionId,
    this.selectedOption,
    this.reveal,
    this.errorCode,
  });

  final bool loading;
  final bool submitting;
  final DecisionCase? caseData;
  final String? sessionId;
  final String? selectedOption;
  final RevealResult? reveal;
  final String? errorCode;

  DecisionState copyWith({
    bool? loading,
    bool? submitting,
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

  @override
  DecisionState build() => const DecisionState();

  Future<void> load() async {
    state = state.copyWith(loading: true, clearError: true);
    try {
      await _repository.ensureGuestCredential();
      final caseData = await _repository.fetchCase(demoCaseId);
      final sessionId = await _repository.startSession(caseData.id);
      state = state.copyWith(
        loading: false,
        caseData: caseData,
        sessionId: sessionId,
        clearError: true,
      );
    } on ApiFailure catch (error) {
      state = state.copyWith(loading: false, errorCode: error.code);
    } catch (_) {
      state = state.copyWith(loading: false, errorCode: 'UNEXPECTED_CLIENT_ERROR');
    }
  }

  void select(String value) {
    if (state.reveal != null || state.submitting) return;
    state = state.copyWith(selectedOption: value, clearError: true);
  }

  Future<void> commit() async {
    final caseData = state.caseData;
    final sessionId = state.sessionId;
    final selected = state.selectedOption;
    if (caseData == null || sessionId == null || selected == null) return;

    state = state.copyWith(submitting: true, clearError: true);
    try {
      final question = caseData.questions.first;
      await _repository.answer(
        sessionId: sessionId,
        questionId: question.id,
        value: selected,
      );
      await _repository.commit(
        sessionId: sessionId,
        idempotencyKey: _idempotencyKey(sessionId),
      );
      final reveal = await _repository.reveal(sessionId);
      state = state.copyWith(
        submitting: false,
        reveal: reveal,
        clearError: true,
      );
    } on ApiFailure catch (error) {
      state = state.copyWith(submitting: false, errorCode: error.code);
    } catch (_) {
      state = state.copyWith(submitting: false, errorCode: 'UNEXPECTED_CLIENT_ERROR');
    }
  }

  String _idempotencyKey(String sessionId) {
    final random = Random.secure().nextInt(1 << 32).toRadixString(16);
    return 'mobile-$sessionId-$random';
  }
}
