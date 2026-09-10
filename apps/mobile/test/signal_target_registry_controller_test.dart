import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/features/impact/application/signal_target_registry_controller.dart';
import 'package:kefe_mobile/features/impact/data/preview_signal_target_registry_repository.dart';
import 'package:kefe_mobile/features/impact/data/signal_target_registry_repository.dart';
import 'package:kefe_mobile/features/impact/domain/signal_target_models.dart';

const _kSignalId = '77777777-7777-4777-8777-777777777701';

/// Fake repository that returns a minimal report immediately.
class _FakeTargetRepository implements SignalTargetRegistryRepository {
  const _FakeTargetRepository();

  @override
  Future<SignalTargetRegistryReportModel> fetchTargetRegistry(
    String signalId,
  ) async {
    return SignalTargetRegistryReportModel(
      signalId: signalId,
      caseVersionId: 'cc000000-0000-4000-8000-000000000099',
      primaryTargetId: 'aa000000-0001-4000-8000-000000000001',
      certifiedAt: '2026-09-10T09:00:00.000000+00:00',
      registryProofHash: 'a' * 64,
      targets: const [
        SignalTargetItemModel(
          targetId: 'aa000000-0001-4000-8000-000000000001',
          targetName: 'Test Kurum A',
          targetType: TargetTypeModel.regulatoryBody,
          jurisdictionLevel: 'NATIONAL',
          officialContactChannel: 'contact@test.gov.tr',
          dispatchStatus: DispatchStatusModel.dispatched,
          responseDueDays: 30,
          dispatchedAt: '2026-09-10T10:00:00+00:00',
        ),
        SignalTargetItemModel(
          targetId: 'bb000000-0002-4000-8000-000000000002',
          targetName: 'Test Kurum B',
          targetType: TargetTypeModel.ministryDepartment,
          jurisdictionLevel: 'NATIONAL',
          officialContactChannel: 'contact2@test.gov.tr',
          dispatchStatus: DispatchStatusModel.actionPledged,
          responseDueDays: 45,
        ),
      ],
    );
  }
}

/// Fake repository that always throws.
class _ErrorTargetRepository implements SignalTargetRegistryRepository {
  const _ErrorTargetRepository();

  @override
  Future<SignalTargetRegistryReportModel> fetchTargetRegistry(
    String signalId,
  ) async {
    throw Exception('Network error');
  }
}

void main() {
  group('SignalTargetRegistryState', () {
    test('hasReport is false when report is null', () {
      const state = SignalTargetRegistryState();
      expect(state.hasReport, isFalse);
      expect(state.hasError, isFalse);
    });

    test('hasReport is true when report is set', () {
      final state = SignalTargetRegistryState(
        report: SignalTargetRegistryReportModel(
          signalId: _kSignalId,
          caseVersionId: 'cc',
          primaryTargetId: 'aa',
          certifiedAt: '2026-09-10T09:00:00+00:00',
          registryProofHash: 'b' * 64,
          targets: const [],
        ),
      );
      expect(state.hasReport, isTrue);
    });

    test('isFullyDispatched is false when targets list is empty', () {
      final state = SignalTargetRegistryState(
        report: SignalTargetRegistryReportModel(
          signalId: _kSignalId,
          caseVersionId: 'cc',
          primaryTargetId: 'aa',
          certifiedAt: '2026-09-10T09:00:00+00:00',
          registryProofHash: 'c' * 64,
          targets: const [],
        ),
      );
      expect(state.isFullyDispatched, isFalse);
    });

    test('isFullyDispatched is true when all targets are terminal', () {
      const state = SignalTargetRegistryState(
        report: SignalTargetRegistryReportModel(
          signalId: _kSignalId,
          caseVersionId: 'cc',
          primaryTargetId: 'aa',
          certifiedAt: '2026-09-10T09:00:00+00:00',
          registryProofHash: 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
          targets: [
            SignalTargetItemModel(
              targetId: 'aa',
              targetName: 'A',
              targetType: TargetTypeModel.regulatoryBody,
              jurisdictionLevel: 'NATIONAL',
              officialContactChannel: 'a@gov.tr',
              dispatchStatus: DispatchStatusModel.actionPledged,
              responseDueDays: 30,
            ),
            SignalTargetItemModel(
              targetId: 'bb',
              targetName: 'B',
              targetType: TargetTypeModel.ministryDepartment,
              jurisdictionLevel: 'NATIONAL',
              officialContactChannel: 'b@gov.tr',
              dispatchStatus: DispatchStatusModel.declinedJurisdiction,
              responseDueDays: 30,
            ),
          ],
        ),
      );
      expect(state.isFullyDispatched, isTrue);
    });

    test('isFullyDispatched is false when any target is non-terminal', () {
      const state = SignalTargetRegistryState(
        report: SignalTargetRegistryReportModel(
          signalId: _kSignalId,
          caseVersionId: 'cc',
          primaryTargetId: 'aa',
          certifiedAt: '2026-09-10T09:00:00+00:00',
          registryProofHash: 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
          targets: [
            SignalTargetItemModel(
              targetId: 'aa',
              targetName: 'A',
              targetType: TargetTypeModel.regulatoryBody,
              jurisdictionLevel: 'NATIONAL',
              officialContactChannel: 'a@gov.tr',
              dispatchStatus: DispatchStatusModel.actionPledged,
              responseDueDays: 30,
            ),
            SignalTargetItemModel(
              targetId: 'bb',
              targetName: 'B',
              targetType: TargetTypeModel.ministryDepartment,
              jurisdictionLevel: 'NATIONAL',
              officialContactChannel: 'b@gov.tr',
              dispatchStatus: DispatchStatusModel.dispatched,
              responseDueDays: 30,
            ),
          ],
        ),
      );
      expect(state.isFullyDispatched, isFalse);
    });
  });

  group('SignalTargetRegistryController (unit)', () {
    ProviderContainer makeContainer(SignalTargetRegistryRepository repo) {
      return ProviderContainer(
        overrides: [
          signalTargetRegistryRepositoryProvider.overrideWithValue(repo),
        ],
      );
    }

    test('loads report from repository', () async {
      final container = makeContainer(const _FakeTargetRepository());
      addTearDown(container.dispose);

      final provider = signalTargetRegistryControllerProviderFor(_kSignalId);
      // Read initial state (loading)
      expect(container.read(provider).loading, isTrue);

      // Wait for microtask + async fetch
      await Future<void>.delayed(Duration.zero);
      await Future<void>.delayed(Duration.zero);

      final state = container.read(provider);
      expect(state.loading, isFalse);
      expect(state.hasReport, isTrue);
      expect(state.report!.signalId, _kSignalId);
      expect(state.report!.targets.length, 2);
    });

    test('sets errorCode on repository failure', () async {
      final container = makeContainer(const _ErrorTargetRepository());
      addTearDown(container.dispose);

      final provider = signalTargetRegistryControllerProviderFor(_kSignalId);
      await Future<void>.delayed(Duration.zero);
      await Future<void>.delayed(Duration.zero);

      final state = container.read(provider);
      expect(state.loading, isFalse);
      expect(state.hasReport, isFalse);
      expect(state.errorCode, 'FAILED_TO_LOAD_TARGET_REGISTRY');
    });
  });

  group('PreviewSignalTargetRegistryRepository', () {
    test('returns a non-empty report for any signalId', () async {
      const repo = PreviewSignalTargetRegistryRepository();
      final report = await repo.fetchTargetRegistry(_kSignalId);
      expect(report.signalId, _kSignalId);
      expect(report.targets.length, 2);
      expect(report.targets.first.dispatchStatus, DispatchStatusModel.dispatched);
      expect(report.targets.last.dispatchStatus, DispatchStatusModel.verifiedTarget);
    });

    test('registryProofHash is exactly 64 characters', () async {
      const repo = PreviewSignalTargetRegistryRepository();
      final report = await repo.fetchTargetRegistry(_kSignalId);
      expect(report.registryProofHash.length, 64);
    });

    test('all preview targets have non-blank targetName and contactChannel', () async {
      const repo = PreviewSignalTargetRegistryRepository();
      final report = await repo.fetchTargetRegistry('any-id');
      for (final t in report.targets) {
        expect(t.targetName, isNotEmpty);
        expect(t.officialContactChannel, isNotEmpty);
        expect(t.responseDueDays, greaterThan(0));
      }
    });
  });
}