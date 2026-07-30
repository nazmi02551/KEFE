import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../decision/application/decision_controller.dart';
import '../../decision/data/decision_repository.dart';
import '../../decision/data/http_decision_repository.dart';
import '../data/consensus_repository.dart';
import '../data/http_consensus_repository.dart';
import '../domain/consensus_models.dart';

enum ConsensusUiState {
  idle,
  loading,
  blocked,
  eligible,
  submitting,
  participated,
  empty,
  errorRetryable,
}

class ConsensusState {
  const ConsensusState({
    this.uiState = ConsensusUiState.idle,
    this.sessionId,
    this.caseVersionId,
    this.cards = const [],
    this.selectedStance,
    this.selectedReasonTags = const {},
    this.errorCode,
  });

  final ConsensusUiState uiState;
  final String? sessionId;
  final String? caseVersionId;
  final List<ConsensusCard> cards;
  final String? selectedStance;
  final Set<String> selectedReasonTags;
  final String? errorCode;

  ConsensusCard? get activeCard {
    for (final card in cards) {
      if (!card.participated) return card;
    }
    return cards.isEmpty ? null : cards.first;
  }

  bool get canSubmit {
    final card = activeCard;
    return uiState == ConsensusUiState.eligible &&
        card != null &&
        !card.participated &&
        selectedStance != null &&
        selectedReasonTags.length <= card.maxReasonTags;
  }

  ConsensusState copyWith({
    ConsensusUiState? uiState,
    String? sessionId,
    String? caseVersionId,
    List<ConsensusCard>? cards,
    String? selectedStance,
    bool clearSelectedStance = false,
    Set<String>? selectedReasonTags,
    String? errorCode,
    bool clearError = false,
  }) {
    return ConsensusState(
      uiState: uiState ?? this.uiState,
      sessionId: sessionId ?? this.sessionId,
      caseVersionId: caseVersionId ?? this.caseVersionId,
      cards: cards ?? this.cards,
      selectedStance:
          clearSelectedStance ? null : selectedStance ?? this.selectedStance,
      selectedReasonTags: selectedReasonTags ?? this.selectedReasonTags,
      errorCode: clearError ? null : errorCode ?? this.errorCode,
    );
  }
}

final consensusRepositoryProvider = Provider<ConsensusRepository>((ref) {
  return HttpConsensusRepository(
    config: ref.watch(appConfigProvider),
    client: ref.watch(httpClientProvider),
    credentialStore: ref.watch(credentialStoreProvider),
  );
});

final consensusControllerProvider =
    NotifierProvider<ConsensusController, ConsensusState>(ConsensusController.new);

class ConsensusController extends Notifier<ConsensusState> {
  ConsensusRepository get _repository => ref.read(consensusRepositoryProvider);
  String? _submissionKey;

  @override
  ConsensusState build() => const ConsensusState();

  Future<void> load({
    required String sessionId,
    required String caseVersionId,
    bool force = false,
  }) async {
    if (!force &&
        state.sessionId == sessionId &&
        state.caseVersionId == caseVersionId &&
        state.uiState != ConsensusUiState.idle &&
        state.uiState != ConsensusUiState.errorRetryable) {
      return;
    }
    state = ConsensusState(
      uiState: ConsensusUiState.loading,
      sessionId: sessionId,
      caseVersionId: caseVersionId,
    );
    _submissionKey = null;
    try {
      final cards = await _repository.fetchCards(
        sessionId: sessionId,
        caseVersionId: caseVersionId,
      );
      state = state.copyWith(
        uiState: _resolvedState(cards),
        cards: cards,
        clearSelectedStance: true,
        selectedReasonTags: const {},
        clearError: true,
      );
    } on ApiFailure catch (error) {
      state = state.copyWith(
        uiState: error.code == 'CONSENSUS_COMMIT_REQUIRED'
            ? ConsensusUiState.blocked
            : ConsensusUiState.errorRetryable,
        errorCode: error.code,
      );
    } on ClientTransportFailure catch (error) {
      state = state.copyWith(
        uiState: ConsensusUiState.errorRetryable,
        errorCode: error.code,
      );
    } catch (_) {
      state = state.copyWith(
        uiState: ConsensusUiState.errorRetryable,
        errorCode: 'CONSENSUS_UNEXPECTED_CLIENT_ERROR',
      );
    }
  }

  void selectStance(String stanceCode) {
    final card = state.activeCard;
    if (card == null || card.participated || !card.stanceCodes.contains(stanceCode)) {
      return;
    }
    state = state.copyWith(selectedStance: stanceCode, clearError: true);
  }

  void toggleReasonTag(String tagCode) {
    final card = state.activeCard;
    if (card == null || card.participated || !card.reasonTagCodes.contains(tagCode)) {
      return;
    }
    final next = {...state.selectedReasonTags};
    if (!next.remove(tagCode)) {
      if (next.length >= card.maxReasonTags) return;
      next.add(tagCode);
    }
    state = state.copyWith(selectedReasonTags: next, clearError: true);
  }

  Future<void> submit() async {
    if (!state.canSubmit) return;
    final card = state.activeCard!;
    final sessionId = state.sessionId!;
    final caseVersionId = state.caseVersionId!;
    _submissionKey ??=
        'mobile-consensus-${DateTime.now().toUtc().microsecondsSinceEpoch}';
    state = state.copyWith(uiState: ConsensusUiState.submitting, clearError: true);
    try {
      final updated = await _repository.participate(
        sessionId: sessionId,
        caseVersionId: caseVersionId,
        cardVersionId: card.versionId,
        stanceCode: state.selectedStance!,
        reasonTagCodes: state.selectedReasonTags.toList(growable: false),
        idempotencyKey: _submissionKey!,
      );
      final cards = [
        for (final item in state.cards)
          if (item.versionId == updated.versionId) updated else item,
      ];
      state = state.copyWith(
        uiState: _resolvedState(cards),
        cards: cards,
        clearError: true,
      );
    } on ApiFailure catch (error) {
      if (error.code == 'CONSENSUS_ALREADY_PARTICIPATED') {
        await load(
          sessionId: sessionId,
          caseVersionId: caseVersionId,
          force: true,
        );
        return;
      }
      state = state.copyWith(
        uiState: ConsensusUiState.errorRetryable,
        errorCode: error.code,
      );
    } on ClientTransportFailure catch (error) {
      state = state.copyWith(
        uiState: ConsensusUiState.errorRetryable,
        errorCode: error.code,
      );
    } catch (_) {
      state = state.copyWith(
        uiState: ConsensusUiState.errorRetryable,
        errorCode: 'CONSENSUS_UNEXPECTED_CLIENT_ERROR',
      );
    }
  }

  Future<void> retry() async {
    final sessionId = state.sessionId;
    final caseVersionId = state.caseVersionId;
    if (sessionId == null || caseVersionId == null) return;
    if (_submissionKey != null && state.selectedStance != null && state.cards.isNotEmpty) {
      state = state.copyWith(uiState: ConsensusUiState.eligible, clearError: true);
      await submit();
      return;
    }
    await load(sessionId: sessionId, caseVersionId: caseVersionId, force: true);
  }

  ConsensusUiState _resolvedState(List<ConsensusCard> cards) {
    if (cards.isEmpty) return ConsensusUiState.empty;
    if (cards.every((card) => card.participated)) {
      return ConsensusUiState.participated;
    }
    return ConsensusUiState.eligible;
  }
}
