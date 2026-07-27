import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../domain/decision_draft.dart';

abstract interface class DecisionDraftStore {
  Future<DecisionDraft?> readForCase(String caseId);
  Future<void> write(DecisionDraft draft);
  Future<void> clearForCase(String caseId);
}

class SharedPreferencesDecisionDraftStore implements DecisionDraftStore {
  SharedPreferencesDecisionDraftStore({SharedPreferences? preferences})
    : _preferences = preferences;

  static const _draftPrefix = 'kefe.decision.draft.v2.';

  SharedPreferences? _preferences;

  Future<SharedPreferences> _prefs() async {
    return _preferences ??= await SharedPreferences.getInstance();
  }

  String _key(String caseId) => '$_draftPrefix$caseId';

  @override
  Future<void> clearForCase(String caseId) async {
    final preferences = await _prefs();
    await preferences.remove(_key(caseId));
  }

  @override
  Future<DecisionDraft?> readForCase(String caseId) async {
    final preferences = await _prefs();
    final key = _key(caseId);
    final raw = preferences.getString(key);
    if (raw == null || raw.isEmpty) return null;

    try {
      final decoded = jsonDecode(raw) as Map<String, Object?>;
      final draft = DecisionDraft.fromJson(decoded);
      if (draft.caseId != caseId) {
        await preferences.remove(key);
        return null;
      }
      return draft;
    } on Object {
      await preferences.remove(key);
      return null;
    }
  }

  @override
  Future<void> write(DecisionDraft draft) async {
    final preferences = await _prefs();
    await preferences.setString(
      _key(draft.caseId),
      jsonEncode(draft.toJson()),
    );
  }
}

class MemoryDecisionDraftStore implements DecisionDraftStore {
  final Map<String, DecisionDraft> drafts = {};

  DecisionDraft? draftFor(String caseId) => drafts[caseId];

  @override
  Future<void> clearForCase(String caseId) async => drafts.remove(caseId);

  @override
  Future<DecisionDraft?> readForCase(String caseId) async => drafts[caseId];

  @override
  Future<void> write(DecisionDraft draft) async => drafts[draft.caseId] = draft;
}
