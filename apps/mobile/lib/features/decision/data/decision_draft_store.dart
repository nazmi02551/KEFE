import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../domain/decision_draft.dart';

abstract interface class DecisionDraftStore {
  Future<DecisionDraft?> readForCase(String caseId);
  Future<void> write(DecisionDraft draft);
  Future<void> clearForCase(String caseId);
}

class SecureDecisionDraftStore implements DecisionDraftStore {
  SecureDecisionDraftStore({
    FlutterSecureStorage? storage,
    SharedPreferences? legacyPreferences,
    DateTime Function()? now,
  }) : _storage = storage ?? const FlutterSecureStorage(),
       _legacyPreferences = legacyPreferences,
       _now = now ?? DateTime.now;

  static const _securePrefix = 'kefe.decision.draft.v3.';
  static const _legacyPrefix = 'kefe.decision.draft.v2.';
  static const draftTtl = Duration(days: 7);

  final FlutterSecureStorage _storage;
  SharedPreferences? _legacyPreferences;
  final DateTime Function() _now;

  String _key(String caseId) => '$_securePrefix$caseId';
  String _legacyKey(String caseId) => '$_legacyPrefix$caseId';

  Future<SharedPreferences> _legacyPrefs() async {
    return _legacyPreferences ??= await SharedPreferences.getInstance();
  }

  @override
  Future<void> clearForCase(String caseId) async {
    await _storage.delete(key: _key(caseId));
    final legacy = await _legacyPrefs();
    await legacy.remove(_legacyKey(caseId));
  }

  @override
  Future<DecisionDraft?> readForCase(String caseId) async {
    final secureKey = _key(caseId);
    var raw = await _storage.read(key: secureKey);

    if (raw == null || raw.isEmpty) {
      final legacy = await _legacyPrefs();
      raw = legacy.getString(_legacyKey(caseId));
      if (raw != null && raw.isNotEmpty) {
        await _storage.write(key: secureKey, value: raw);
        await legacy.remove(_legacyKey(caseId));
      }
    }
    if (raw == null || raw.isEmpty) return null;

    try {
      final decoded = jsonDecode(raw) as Map<String, Object?>;
      final draft = DecisionDraft.fromJson(decoded);
      if (draft.caseId != caseId || _isExpiredUncommittedDraft(draft)) {
        await clearForCase(caseId);
        return null;
      }
      return draft;
    } on Object {
      await clearForCase(caseId);
      return null;
    }
  }

  bool _isExpiredUncommittedDraft(DecisionDraft draft) {
    // commitPending/committedAwaitingReveal are server-authoritative recovery
    // states and must not be deleted merely because the local clock crossed TTL.
    if (draft.phase == DecisionDraftPhase.commitPending ||
        draft.phase == DecisionDraftPhase.committedAwaitingReveal) {
      return false;
    }
    final age = _now().toUtc().difference(draft.updatedAt.toUtc());
    return age > draftTtl;
  }

  @override
  Future<void> write(DecisionDraft draft) async {
    await _storage.write(
      key: _key(draft.caseId),
      value: jsonEncode(draft.toJson()),
    );
  }
}

/// Legacy adapter retained only for backwards-compatible tests/migrations.
/// Production composition uses [SecureDecisionDraftStore].
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
