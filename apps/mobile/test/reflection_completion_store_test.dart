import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/features/decision/data/reflection_completion_store.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  test('Reflection completion cursor survives store re-instantiation', () async {
    final firstStore = SharedPreferencesReflectionCompletionStore();
    const pending = PendingReflectionCompletion(
      sessionId: 'session-1',
      caseVersionId: 'case-version-1',
      stepCode: 'REFLECTION',
      latestRevisionId: 'revision-2',
      idempotencyKey: 'reflection-key-1',
    );

    await firstStore.write(pending);

    final restored = await SharedPreferencesReflectionCompletionStore().read(
      sessionId: 'session-1',
      stepCode: 'REFLECTION',
    );

    expect(restored, isNotNull);
    expect(restored!.caseVersionId, 'case-version-1');
    expect(restored.latestRevisionId, 'revision-2');
    expect(restored.idempotencyKey, 'reflection-key-1');
  });

  test('Reflection completion cursor can be cleared after acknowledgement', () async {
    final store = SharedPreferencesReflectionCompletionStore();
    await store.write(
      const PendingReflectionCompletion(
        sessionId: 'session-2',
        caseVersionId: 'case-version-2',
        stepCode: 'REFLECTION',
        latestRevisionId: 'revision-3',
        idempotencyKey: 'reflection-key-2',
      ),
    );

    await store.clear(sessionId: 'session-2', stepCode: 'REFLECTION');

    expect(
      await SharedPreferencesReflectionCompletionStore().read(
        sessionId: 'session-2',
        stepCode: 'REFLECTION',
      ),
      isNull,
    );
  });
}
