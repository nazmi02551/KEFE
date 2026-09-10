import '../domain/signal_target_models.dart';
import 'signal_target_registry_repository.dart';

/// Preview/test fixture adapter for [SignalTargetRegistryRepository].
///
/// Returns deterministic, locale-neutral fixture data for a given [signalId].
/// Used in Product Preview builds and widget tests.
///
/// Invariants:
/// - Does not call any network endpoint.
/// - Returns a stable [SignalTargetRegistryReportModel] with two targets:
///   one VERIFIED_TARGET and one DISPATCHED — sufficient to exercise all
///   dispatch status states in the [SignalTargetRegistryCard] widget.
/// - Preview fixtures must never become a production fallback.
class PreviewSignalTargetRegistryRepository
    implements SignalTargetRegistryRepository {
  const PreviewSignalTargetRegistryRepository();

  static const _kPreviewTargetA = 'aaaaaaaa-0001-4aaa-8aaa-000000000001';
  static const _kPreviewTargetB = 'bbbbbbbb-0002-4bbb-8bbb-000000000002';

  @override
  Future<SignalTargetRegistryReportModel> fetchTargetRegistry(
    String signalId,
  ) async {
    // Simulate minimal network latency in preview
    await Future<void>.delayed(const Duration(milliseconds: 180));

    return SignalTargetRegistryReportModel(
      signalId: signalId,
      caseVersionId: 'cccccccc-0000-4ccc-8ccc-000000000099',
      primaryTargetId: _kPreviewTargetA,
      certifiedAt: '2026-09-10T09:00:00.000000+00:00',
      registryProofHash:
          'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
      targets: const [
        SignalTargetItemModel(
          targetId: _kPreviewTargetA,
          targetName: 'Kamu İhale Kurumu',
          targetType: TargetTypeModel.regulatoryBody,
          jurisdictionLevel: 'NATIONAL',
          officialContactChannel: 'kik-iletisim@kik.gov.tr',
          dispatchStatus: DispatchStatusModel.dispatched,
          responseDueDays: 30,
          dispatchedAt: '2026-09-10T10:30:00.000000+00:00',
        ),
        SignalTargetItemModel(
          targetId: _kPreviewTargetB,
          targetName: 'Hazine ve Maliye Bakanlığı',
          targetType: TargetTypeModel.ministryDepartment,
          jurisdictionLevel: 'NATIONAL',
          officialContactChannel: 'iletisim@hmb.gov.tr',
          dispatchStatus: DispatchStatusModel.verifiedTarget,
          responseDueDays: 45,
        ),
      ],
    );
  }
}