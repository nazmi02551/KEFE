import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/features/saved_cases/data/saved_case_store.dart';
import 'package:kefe_mobile/features/saved_cases/domain/saved_case.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  test('persists version-pinned saved Cases newest first', () async {
    final store = SharedPreferencesSavedCaseStore();
    final older = SavedCase(
      caseId: 'case-1',
      caseVersionId: 'version-1',
      title: 'İlk vaka',
      summary: 'İlk özet',
      domain: 'DAILY_LIFE',
      format: 'DILEMMA',
      risk: 'L0',
      savedAt: DateTime.utc(2026, 7, 29, 10),
    );
    final newer = SavedCase(
      caseId: 'case-2',
      caseVersionId: 'version-2',
      title: 'İkinci vaka',
      summary: 'İkinci özet',
      domain: 'TECHNOLOGY',
      format: 'DILEMMA',
      risk: 'L0',
      savedAt: DateTime.utc(2026, 7, 30, 10),
    );

    await store.writeAll([older, newer]);
    final restored = await SharedPreferencesSavedCaseStore().readAll();

    expect(restored.map((item) => item.caseId), ['case-2', 'case-1']);
    expect(restored.first.caseVersionId, 'version-2');
  });

  test('drops invalid or corrupt saved data safely', () async {
    SharedPreferences.setMockInitialValues({
      'kefe.saved_cases.v1': '[{"case_id":""}]',
    });

    final restored = await SharedPreferencesSavedCaseStore().readAll();

    expect(restored, isEmpty);
  });
}
