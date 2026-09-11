import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../decision/domain/decision_models.dart';
import '../data/saved_case_store.dart';
import '../domain/saved_case.dart';

final savedCaseStoreProvider = Provider<SavedCaseStore>((ref) {
  return SharedPreferencesSavedCaseStore();
});

enum SavedCasesUiState { idle, loading, ready, error }

class SavedCasesState {
  const SavedCasesState({
    this.uiState = SavedCasesUiState.idle,
    this.items = const [],
    this.updatedCaseIds = const {},
  });

  final SavedCasesUiState uiState;
  final List<SavedCase> items;

  /// Set of caseIds where the catalog version differs from the saved snapshot.
  ///
  /// Only populated after a successful foreground catalog comparison
  /// (see SavedCasesController.reconcileWithCatalog).
  /// Empty when catalog has not been fetched or fetch failed (ADR-0139:
  /// unknown state must not be described as deletion or update).
  final Set<String> updatedCaseIds;

  bool contains(String caseId) => items.any((item) => item.caseId == caseId);

  /// True when the saved snapshot for [caseId] has a newer catalog version.
  bool hasUpdate(String caseId) => updatedCaseIds.contains(caseId);

  /// Number of saved cases with a newer catalog version available.
  int get updateCount => updatedCaseIds.length;
}

final savedCasesControllerProvider =
    NotifierProvider<SavedCasesController, SavedCasesState>(
      SavedCasesController.new,
    );

class SavedCasesController extends Notifier<SavedCasesState> {
  SavedCaseStore get _store => ref.read(savedCaseStoreProvider);

  @override
  SavedCasesState build() => const SavedCasesState();

  Future<void> load() async {
    if (state.uiState == SavedCasesUiState.loading) return;
    state = SavedCasesState(
      uiState: SavedCasesUiState.loading,
      items: state.items,
    );
    try {
      final items = await _store.readAll();
      state = SavedCasesState(
        uiState: SavedCasesUiState.ready,
        items: items,
        // Clear update markers on reload — catalog must be re-compared
        updatedCaseIds: const {},
      );
    } on Object {
      state = SavedCasesState(
        uiState: SavedCasesUiState.error,
        items: state.items,
        updatedCaseIds: state.updatedCaseIds,
      );
    }
  }

  Future<void> toggle(DecisionCaseSummary summary) async {
    final next = [...state.items];
    final index = next.indexWhere((item) => item.caseId == summary.id);
    if (index >= 0) {
      next.removeAt(index);
    } else {
      next.insert(0, SavedCase.fromSummary(summary));
    }
    state = SavedCasesState(
      uiState: SavedCasesUiState.ready,
      items: next,
      updatedCaseIds: state.updatedCaseIds,
    );
    try {
      await _store.writeAll(next);
    } on Object {
      await load();
    }
  }

  Future<void> remove(String caseId) async {
    final next = state.items
        .where((item) => item.caseId != caseId)
        .toList(growable: false);
    final updatedIds = {...state.updatedCaseIds}..remove(caseId);
    state = SavedCasesState(
      uiState: SavedCasesUiState.ready,
      items: next,
      updatedCaseIds: updatedIds,
    );
    try {
      await _store.writeAll(next);
    } on Object {
      await load();
    }
  }

  /// Compares saved snapshots against a successfully fetched catalog.
  ///
  /// A saved Case has a lifecycle update only when the catalog contains the
  /// same exact Case id AND its current case_version_id differs from the
  /// stored snapshot (ADR-0139 decision boundary).
  ///
  /// [catalogSummaries] must represent a successful catalog response.
  /// Calling this method with an empty list or after a failed fetch is a
  /// caller error — use the no-argument overload to clear update markers when
  /// the catalog is unavailable.
  void reconcileWithCatalog(List<DecisionCaseSummary> catalogSummaries) {
    final catalogIndex = {
      for (final s in catalogSummaries) s.id: s.versionId,
    };
    final updated = <String>{};
    for (final saved in state.items) {
      final catalogVersion = catalogIndex[saved.caseId];
      if (catalogVersion != null && catalogVersion != saved.caseVersionId) {
        updated.add(saved.caseId);
      }
    }
    state = SavedCasesState(
      uiState: state.uiState,
      items: state.items,
      updatedCaseIds: updated,
    );
  }

  /// Clears lifecycle update markers without changing persisted state.
  ///
  /// Called when the catalog fetch fails or is unavailable — unknown state
  /// must not be displayed as deletion or update (ADR-0139).
  void clearUpdateMarkers() {
    if (state.updatedCaseIds.isEmpty) return;
    state = SavedCasesState(
      uiState: state.uiState,
      items: state.items,
    );
  }

  Future<void> acknowledgeCurrentVersion(DecisionCaseSummary summary) async {
    final next = [...state.items];
    final index = next.indexWhere((item) => item.caseId == summary.id);
    if (index < 0 || next[index].caseVersionId == summary.versionId) return;

    final savedAt = next[index].savedAt;
    next[index] = SavedCase.fromSummary(summary, savedAt: savedAt);
    // Remove update marker for this case on acknowledgement
    final updatedIds = {...state.updatedCaseIds}..remove(summary.id);
    state = SavedCasesState(
      uiState: SavedCasesUiState.ready,
      items: next,
      updatedCaseIds: updatedIds,
    );
    try {
      await _store.writeAll(next);
    } on Object {
      await load();
    }
  }
}
