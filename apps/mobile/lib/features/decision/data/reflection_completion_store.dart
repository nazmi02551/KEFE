import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

class PendingReflectionCompletion {
  const PendingReflectionCompletion({
    required this.sessionId,
    required this.caseVersionId,
    required this.stepCode,
    required this.latestRevisionId,
    required this.idempotencyKey,
  });

  final String sessionId;
  final String caseVersionId;
  final String stepCode;
  final String latestRevisionId;
  final String idempotencyKey;

  Map<String, Object?> toJson() => {
    'session_id': sessionId,
    'case_version_id': caseVersionId,
    'step_code': stepCode,
    'latest_revision_id': latestRevisionId,
    'idempotency_key': idempotencyKey,
  };

  factory PendingReflectionCompletion.fromJson(Map<String, Object?> json) {
    return PendingReflectionCompletion(
      sessionId: json['session_id'] as String,
      caseVersionId: json['case_version_id'] as String,
      stepCode: json['step_code'] as String,
      latestRevisionId: json['latest_revision_id'] as String,
      idempotencyKey: json['idempotency_key'] as String,
    );
  }
}

abstract interface class ReflectionCompletionStore {
  Future<PendingReflectionCompletion?> read({
    required String sessionId,
    required String stepCode,
  });

  Future<void> write(PendingReflectionCompletion completion);

  Future<void> clear({
    required String sessionId,
    required String stepCode,
  });
}

class SharedPreferencesReflectionCompletionStore
    implements ReflectionCompletionStore {
  SharedPreferencesReflectionCompletionStore({SharedPreferences? preferences})
    : _preferences = preferences;

  static const _prefix = 'kefe.reflection.completion.v1.';

  SharedPreferences? _preferences;

  Future<SharedPreferences> _prefs() async {
    return _preferences ??= await SharedPreferences.getInstance();
  }

  String _key(String sessionId, String stepCode) =>
      '$_prefix$sessionId.$stepCode';

  @override
  Future<PendingReflectionCompletion?> read({
    required String sessionId,
    required String stepCode,
  }) async {
    final preferences = await _prefs();
    final key = _key(sessionId, stepCode);
    final raw = preferences.getString(key);
    if (raw == null || raw.isEmpty) return null;
    try {
      final completion = PendingReflectionCompletion.fromJson(
        (jsonDecode(raw) as Map).cast<String, Object?>(),
      );
      if (completion.sessionId != sessionId || completion.stepCode != stepCode) {
        await preferences.remove(key);
        return null;
      }
      return completion;
    } on Object {
      await preferences.remove(key);
      return null;
    }
  }

  @override
  Future<void> write(PendingReflectionCompletion completion) async {
    final preferences = await _prefs();
    await preferences.setString(
      _key(completion.sessionId, completion.stepCode),
      jsonEncode(completion.toJson()),
    );
  }

  @override
  Future<void> clear({
    required String sessionId,
    required String stepCode,
  }) async {
    final preferences = await _prefs();
    await preferences.remove(_key(sessionId, stepCode));
  }
}

class MemoryReflectionCompletionStore implements ReflectionCompletionStore {
  final Map<String, PendingReflectionCompletion> completions = {};

  String _key(String sessionId, String stepCode) => '$sessionId:$stepCode';

  @override
  Future<PendingReflectionCompletion?> read({
    required String sessionId,
    required String stepCode,
  }) async => completions[_key(sessionId, stepCode)];

  @override
  Future<void> write(PendingReflectionCompletion completion) async {
    completions[_key(completion.sessionId, completion.stepCode)] = completion;
  }

  @override
  Future<void> clear({
    required String sessionId,
    required String stepCode,
  }) async {
    completions.remove(_key(sessionId, stepCode));
  }
}
