import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../decision/application/decision_controller.dart';
import '../../decision/data/decision_repository.dart';
import '../data/community_reason_repository.dart';
import '../data/http_community_reason_repository.dart';

final communityReasonExperienceEnabledProvider = Provider<bool>((ref) => false);

final communityReasonRepositoryProvider = Provider<CommunityReasonRepository>((ref) {
  if (!ref.watch(communityReasonExperienceEnabledProvider)) {
    return const _DisabledCommunityReasonRepository();
  }
  return HttpCommunityReasonRepository(
    config: ref.watch(appConfigProvider),
    client: ref.watch(httpClientProvider),
    credentialStore: ref.watch(credentialStoreProvider),
  );
});

enum CommunityReasonUiState { idle, loading, ready, submitting, error }

class CommunityReasonState {
  const CommunityReasonState({
    this.uiState = CommunityReasonUiState.idle,
    this.snapshot,
    this.receipt,
    this.selectedTags = const {},
    this.text = '',
    this.errorCode,
  });

  final CommunityReasonUiState uiState;
  final CommunityReasonSnapshot? snapshot;
  final CommunityReasonReceipt? receipt;
  final Set<String> selectedTags;
  final String text;
  final String? errorCode;

  CommunityReasonState copyWith({
    CommunityReasonUiState? uiState,
    CommunityReasonSnapshot? snapshot,
    CommunityReasonReceipt? receipt,
    Set<String>? selectedTags,
    String? text,
    String? errorCode,
    bool clearError = false,
  }) => CommunityReasonState(
    uiState: uiState ?? this.uiState,
    snapshot: snapshot ?? this.snapshot,
    receipt: receipt ?? this.receipt,
    selectedTags: selectedTags ?? this.selectedTags,
    text: text ?? this.text,
    errorCode: clearError ? null : errorCode ?? this.errorCode,
  );
}

final communityReasonControllerProvider = NotifierProvider<
    CommunityReasonController,
    CommunityReasonState>(CommunityReasonController.new);

class CommunityReasonController extends Notifier<CommunityReasonState> {
  CommunityReasonRepository get _repository => ref.read(communityReasonRepositoryProvider);
  String? _caseVersionId;

  @override
  CommunityReasonState build() => const CommunityReasonState();

  Future<void> load(String caseVersionId) async {
    if (_caseVersionId == caseVersionId &&
        state.uiState == CommunityReasonUiState.ready) {
      return;
    }
    _caseVersionId = caseVersionId;
    state = state.copyWith(uiState: CommunityReasonUiState.loading, clearError: true);
    try {
      final snapshot = await _repository.fetch(caseVersionId);
      state = state.copyWith(
        uiState: CommunityReasonUiState.ready,
        snapshot: snapshot,
        clearError: true,
      );
    } on ApiFailure catch (error) {
      state = state.copyWith(uiState: CommunityReasonUiState.error, errorCode: error.code);
    } on ClientTransportFailure catch (error) {
      state = state.copyWith(uiState: CommunityReasonUiState.error, errorCode: error.code);
    }
  }

  void toggleTag(String tag, {int maxTags = 3}) {
    final next = {...state.selectedTags};
    if (!next.remove(tag)) {
      if (next.length >= maxTags) return;
      next.add(tag);
    }
    state = state.copyWith(selectedTags: next, clearError: true);
  }

  void setText(String value) {
    state = state.copyWith(text: value, clearError: true);
  }

  Future<void> publish(String sessionId) async {
    if (state.selectedTags.isEmpty || state.uiState == CommunityReasonUiState.submitting) {
      return;
    }
    state = state.copyWith(uiState: CommunityReasonUiState.submitting, clearError: true);
    try {
      final receipt = await _repository.publish(
        sessionId: sessionId,
        tags: state.selectedTags.toList(growable: false),
        text: state.text.trim().isEmpty ? null : state.text.trim(),
      );
      final caseVersionId = _caseVersionId;
      CommunityReasonSnapshot? snapshot = state.snapshot;
      if (caseVersionId != null) {
        snapshot = await _repository.fetch(caseVersionId);
      }
      state = state.copyWith(
        uiState: CommunityReasonUiState.ready,
        receipt: receipt,
        snapshot: snapshot,
        selectedTags: const {},
        text: '',
        clearError: true,
      );
    } on ApiFailure catch (error) {
      state = state.copyWith(uiState: CommunityReasonUiState.error, errorCode: error.code);
    } on ClientTransportFailure catch (error) {
      state = state.copyWith(uiState: CommunityReasonUiState.error, errorCode: error.code);
    }
  }

  Future<void> react(String reasonId, String reaction) async {
    try {
      await _repository.react(reasonId: reasonId, reaction: reaction);
      if (_caseVersionId != null) {
        final snapshot = await _repository.fetch(_caseVersionId!);
        state = state.copyWith(snapshot: snapshot, clearError: true);
      }
    } on ApiFailure catch (error) {
      state = state.copyWith(errorCode: error.code);
    } on ClientTransportFailure catch (error) {
      state = state.copyWith(errorCode: error.code);
    }
  }

  Future<void> report(String reasonId) async {
    try {
      await _repository.report(reasonId: reasonId, code: 'OTHER');
    } on ApiFailure catch (error) {
      state = state.copyWith(errorCode: error.code);
    } on ClientTransportFailure catch (error) {
      state = state.copyWith(errorCode: error.code);
    }
  }
}

class _DisabledCommunityReasonRepository implements CommunityReasonRepository {
  const _DisabledCommunityReasonRepository();

  @override
  Future<CommunityReasonSnapshot> fetch(String caseVersionId) async =>
      const CommunityReasonSnapshot(
        items: [],
        tagPatternCounts: {},
        sampleSize: 0,
        methodologyNote: '',
      );

  @override
  Future<CommunityReasonReceipt> publish({
    required String sessionId,
    required List<String> tags,
    String? text,
  }) => throw const ClientTransportFailure(code: 'COMMUNITY_REASON_NOT_ENABLED');

  @override
  Future<void> react({required String reasonId, required String reaction}) =>
      throw const ClientTransportFailure(code: 'COMMUNITY_REASON_NOT_ENABLED');

  @override
  Future<void> report({required String reasonId, required String code}) =>
      throw const ClientTransportFailure(code: 'COMMUNITY_REASON_NOT_ENABLED');
}
