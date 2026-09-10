import '../domain/signal_target_models.dart';

/// Abstract repository for signal dispatch target registry.
///
/// Exposes read-only access to the [SignalTargetRegistryReportModel] for a
/// given [signalId]. The registry is computed server-side from the
/// signal.dispatch_target_registry table (migration 0043).
abstract class SignalTargetRegistryRepository {
  /// Returns the dispatch target registry report for [signalId].
  ///
  /// Throws [ApiFailure] (or equivalent) when the request fails or the
  /// signal is not found.
  Future<SignalTargetRegistryReportModel> fetchTargetRegistry(String signalId);
}
