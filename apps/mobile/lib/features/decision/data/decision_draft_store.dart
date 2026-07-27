import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../domain/decision_draft.dart';

abstract interface class DecisionDraftStore {
  Future<DecisionDraft?> read();
  Future<void> write(DecisionDraft draft);
  Future<void> clear();
}

class SharedPreferencesDecisionDraftStore implements DecisionDraftStore {
  SharedPreferencesDecisionDraftStore({SharedPreferences? preferences})
    : _preferences = preferences;

  static const _draftKey = 'kefe.decision.draft.v1';

  SharedPreferences? _preferences;

  Future<SharedPreferences> _prefs() async {
    return _preferences ??= await SharedPreferences.getInstance();
  }

  @override
  Future<void> clear() async {
    final preferences = await _prefs();
    await preferences.remove(_draftKey);
  }

  @override
  Future<DecisionDraft?> read() async {
    final preferences = await _prefs();
    final raw = preferences.getString(_draftKey);
    if (raw == null || raw.isEmpty) return null;

    try {
      final decoded = jsonDecode(raw) as Map<String, Object?>;
      return DecisionDraft.fromJson(decoded);
    } on Object {
      await preferences.remove(_draftKey);
      return null;
    }
  }

  @override
  Future<void> write(DecisionDraft draft) async {
    final preferences = await _prefs();
    await preferences.setString(_draftKey, jsonEncode(draft.toJson()));
  }
}

class MemoryDecisionDraftStore implements DecisionDraftStore {
  DecisionDraft? draft;

  @override
  Future<void> clear() async => draft = null;

  @override
  Future<DecisionDraft?> read() async => draft;

  @override
  Future<void> write(DecisionDraft draft) async => this.draft = draft;
}
