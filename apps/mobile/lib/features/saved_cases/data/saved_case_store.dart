import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../domain/saved_case.dart';

abstract interface class SavedCaseStore {
  Future<List<SavedCase>> readAll();
  Future<void> writeAll(List<SavedCase> items);
}

class SharedPreferencesSavedCaseStore implements SavedCaseStore {
  SharedPreferencesSavedCaseStore({SharedPreferences? preferences})
      : _preferences = preferences;

  static const _key = 'kefe.saved_cases.v1';

  SharedPreferences? _preferences;

  Future<SharedPreferences> _prefs() async {
    return _preferences ??= await SharedPreferences.getInstance();
  }

  @override
  Future<List<SavedCase>> readAll() async {
    final preferences = await _prefs();
    final raw = preferences.getString(_key);
    if (raw == null || raw.isEmpty) return const [];

    try {
      final decoded = jsonDecode(raw) as List<Object?>;
      final byCaseId = <String, SavedCase>{};
      for (final item in decoded) {
        if (item is! Map) continue;
        final saved = SavedCase.fromJson(item.cast<String, Object?>());
        if (!saved.isValid) continue;
        final current = byCaseId[saved.caseId];
        if (current == null || saved.savedAt.isAfter(current.savedAt)) {
          byCaseId[saved.caseId] = saved;
        }
      }
      final items = byCaseId.values.toList(growable: false)
        ..sort((a, b) => b.savedAt.compareTo(a.savedAt));
      return items;
    } on Object {
      await preferences.remove(_key);
      return const [];
    }
  }

  @override
  Future<void> writeAll(List<SavedCase> items) async {
    final preferences = await _prefs();
    final normalized = [...items]..sort((a, b) => b.savedAt.compareTo(a.savedAt));
    await preferences.setString(
      _key,
      jsonEncode(normalized.map((item) => item.toJson()).toList(growable: false)),
    );
  }
}

class MemorySavedCaseStore implements SavedCaseStore {
  MemorySavedCaseStore([Iterable<SavedCase> initial = const []])
      : items = List<SavedCase>.from(initial);

  List<SavedCase> items;

  @override
  Future<List<SavedCase>> readAll() async => List.unmodifiable(items);

  @override
  Future<void> writeAll(List<SavedCase> value) async {
    items = List<SavedCase>.from(value);
  }
}