// ADR-0139 / CAP-079 — SavedCasesController reconcileWithCatalog unit tests.
//
// Verifies the exact lifecycle update detection logic:
//   "EXACT_CASE_ID_MATCH_AND_CASE_VERSION_ID_DIFFERS"
// and truthfulness constraints:
//   "CATALOG_FAILURE = UNKNOWN_NO_UPDATE_CLAIM"
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';
import 'package:kefe_mobile/features/saved_cases/application/saved_cases_controller.dart';
import 'package:kefe_mobile/features/saved_cases/data/saved_case_store.dart';
import 'package:kefe_mobile/features/saved_cases/domain/saved_case.dart';

const _caseId1 = 'case-0001';
const _caseId2 = 'case-0002';
const _caseId3 = 'case-0003';
const _vOld = 'version-old';
const _vNew = 'version-new';

SavedCase _savedCase({
  required String caseId,
  required String versionId,
}) =>
    SavedCase(
      caseId: caseId,
      caseVersionId: versionId,
      title: 'Test Vakası $caseId',
      summary: 'özet',
      domain: 'GOVERNANCE',
      format: 'DEBATE',
      risk: 'LOW',
      savedAt: DateTime.utc(2026, 9, 1),
    );

DecisionCaseSummary _catalogSummary({
  required String caseId,
  required String versionId,
}) =>
    DecisionCaseSummary(
      id: caseId,
      versionId: versionId,
      title: 'Catalog $caseId',
      summary: 'özet',
      domain: 'GOVERNANCE',
      format: 'DEBATE',
      risk: 'LOW',
    );

ProviderContainer _container(List<SavedCase> saved) {
  final store = MemorySavedCaseStore(saved);
  return ProviderContainer(
    overrides: [savedCaseStoreProvider.overrideWithValue(store)],
  );
}

void main() {
  group('SavedCasesController.reconcileWithCatalog (ADR-0139)', () {
    test('no updates when catalog matches saved versions exactly', () async {
      final container = _container([
        _savedCase(caseId: _caseId1, versionId: _vOld),
      ]);
      addTearDown(container.dispose);
      await container.read(savedCasesControllerProvider.notifier).load();

      container.read(savedCasesControllerProvider.notifier).reconcileWithCatalog([
        _catalogSummary(caseId: _caseId1, versionId: _vOld),
      ]);

      final state = container.read(savedCasesControllerProvider);
      expect(state.updatedCaseIds, isEmpty);
      expect(state.updateCount, 0);
      expect(state.hasUpdate(_caseId1), isFalse);
    });

    test('marks update when catalog version differs from saved snapshot', () async {
      final container = _container([
        _savedCase(caseId: _caseId1, versionId: _vOld),
      ]);
      addTearDown(container.dispose);
      await container.read(savedCasesControllerProvider.notifier).load();

      container.read(savedCasesControllerProvider.notifier).reconcileWithCatalog([
        _catalogSummary(caseId: _caseId1, versionId: _vNew),
      ]);

      final state = container.read(savedCasesControllerProvider);
      expect(state.hasUpdate(_caseId1), isTrue);
      expect(state.updateCount, 1);
    });

    test('marks only the case with a differing version, not all cases', () async {
      final container = _container([
        _savedCase(caseId: _caseId1, versionId: _vOld),
        _savedCase(caseId: _caseId2, versionId: _vOld),
        _savedCase(caseId: _caseId3, versionId: _vOld),
      ]);
      addTearDown(container.dispose);
      await container.read(savedCasesControllerProvider.notifier).load();

      container.read(savedCasesControllerProvider.notifier).reconcileWithCatalog([
        _catalogSummary(caseId: _caseId1, versionId: _vNew), // updated
        _catalogSummary(caseId: _caseId2, versionId: _vOld), // same
        // _caseId3 not in catalog
      ]);

      final state = container.read(savedCasesControllerProvider);
      expect(state.hasUpdate(_caseId1), isTrue);
      expect(state.hasUpdate(_caseId2), isFalse);
      expect(state.hasUpdate(_caseId3), isFalse); // not in catalog = unknown
      expect(state.updateCount, 1);
    });

    test('case not in catalog is unknown state (no update claim)', () async {
      final container = _container([
        _savedCase(caseId: _caseId1, versionId: _vOld),
      ]);
      addTearDown(container.dispose);
      await container.read(savedCasesControllerProvider.notifier).load();

      // Catalog does not include _caseId1
      container.read(savedCasesControllerProvider.notifier).reconcileWithCatalog([
        _catalogSummary(caseId: _caseId2, versionId: _vNew),
      ]);

      final state = container.read(savedCasesControllerProvider);
      expect(state.hasUpdate(_caseId1), isFalse);
      expect(state.updateCount, 0);
    });

    test('clearUpdateMarkers removes all update claims without persisted change',
        () async {
      final container = _container([
        _savedCase(caseId: _caseId1, versionId: _vOld),
      ]);
      addTearDown(container.dispose);
      await container.read(savedCasesControllerProvider.notifier).load();

      container.read(savedCasesControllerProvider.notifier).reconcileWithCatalog([
        _catalogSummary(caseId: _caseId1, versionId: _vNew),
      ]);
      expect(
        container.read(savedCasesControllerProvider).hasUpdate(_caseId1),
        isTrue,
      );

      container.read(savedCasesControllerProvider.notifier).clearUpdateMarkers();

      final state = container.read(savedCasesControllerProvider);
      expect(state.updatedCaseIds, isEmpty);
      expect(state.updateCount, 0);
    });

    test('acknowledgeCurrentVersion removes update marker for that case', () async {
      final container = _container([
        _savedCase(caseId: _caseId1, versionId: _vOld),
        _savedCase(caseId: _caseId2, versionId: _vOld),
      ]);
      addTearDown(container.dispose);
      await container.read(savedCasesControllerProvider.notifier).load();

      container.read(savedCasesControllerProvider.notifier).reconcileWithCatalog([
        _catalogSummary(caseId: _caseId1, versionId: _vNew),
        _catalogSummary(caseId: _caseId2, versionId: _vNew),
      ]);
      expect(
        container.read(savedCasesControllerProvider).updateCount,
        2,
      );

      await container
          .read(savedCasesControllerProvider.notifier)
          .acknowledgeCurrentVersion(
            _catalogSummary(caseId: _caseId1, versionId: _vNew),
          );

      final state = container.read(savedCasesControllerProvider);
      expect(state.hasUpdate(_caseId1), isFalse); // acknowledged
      expect(state.hasUpdate(_caseId2), isTrue);  // still pending
      expect(state.updateCount, 1);
    });

    test('remove clears update marker for removed case', () async {
      final container = _container([
        _savedCase(caseId: _caseId1, versionId: _vOld),
      ]);
      addTearDown(container.dispose);
      await container.read(savedCasesControllerProvider.notifier).load();

      container.read(savedCasesControllerProvider.notifier).reconcileWithCatalog([
        _catalogSummary(caseId: _caseId1, versionId: _vNew),
      ]);
      expect(
        container.read(savedCasesControllerProvider).hasUpdate(_caseId1),
        isTrue,
      );

      await container
          .read(savedCasesControllerProvider.notifier)
          .remove(_caseId1);

      final state = container.read(savedCasesControllerProvider);
      expect(state.hasUpdate(_caseId1), isFalse);
      expect(state.updateCount, 0);
    });

    test('reconcile with empty catalog clears all update markers', () async {
      final container = _container([
        _savedCase(caseId: _caseId1, versionId: _vOld),
      ]);
      addTearDown(container.dispose);
      await container.read(savedCasesControllerProvider.notifier).load();

      container.read(savedCasesControllerProvider.notifier).reconcileWithCatalog([
        _catalogSummary(caseId: _caseId1, versionId: _vNew),
      ]);
      expect(
        container.read(savedCasesControllerProvider).updateCount,
        1,
      );

      // Empty catalog = no matches = no updates
      container
          .read(savedCasesControllerProvider.notifier)
          .reconcileWithCatalog([]);

      expect(container.read(savedCasesControllerProvider).updateCount, 0);
    });
  });
}