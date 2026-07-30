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
  });

  final SavedCasesUiState uiState;
  final List<SavedCase> items;

  bool contains(String caseId) => items.any((item) => item.caseId == caseId);
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
      state = SavedCasesState(uiState: SavedCasesUiState.ready, items: items);
    } on Object {
      state = SavedCasesState(
        uiState: SavedCasesUiState.error,
        items: state.items,
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
    state = SavedCasesState(uiState: SavedCasesUiState.ready, items: next);
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
    state = SavedCasesState(uiState: SavedCasesUiState.ready, items: next);
    try {
      await _store.writeAll(next);
    } on Object {
      await load();
    }
  }
}
