import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/signal_target_registry_repository.dart';
import '../domain/signal_target_models.dart';

/// State for [SignalTargetRegistryController].
///
/// [loading] is true while the registry is being fetched.
/// [report] is non-null after a successful fetch.
/// [errorCode] is set when the fetch fails.
class SignalTargetRegistryState {
  const SignalTargetRegistryState({
    this.loading = false,
    this.report,
    this.errorCode,
  });

  final bool loading;
  final SignalTargetRegistryReportModel? report;
  final String? errorCode;

  bool get hasReport => report != null;
  bool get hasError => errorCode != null;

  /// True when every target has reached a terminal dispatch state.
  bool get isFullyDispatched {
    final r = report;
    if (r == null || r.targets.isEmpty) return false;
    const terminalStatuses = {
      DispatchStatusModel.actionPledged,
      DispatchStatusModel.declinedJurisdiction,
    };
    return r.targets.every((t) => terminalStatuses.contains(t.dispatchStatus));
  }
}

/// Per-signalId provider factory.
///
/// Usage:
///   final provider = signalTargetRegistryControllerProviderFor(signalId);
///   ref.watch(provider)
NotifierProvider<SignalTargetRegistryController, SignalTargetRegistryState>
    signalTargetRegistryControllerProviderFor(String signalId) =>
        NotifierProvider<SignalTargetRegistryController,
            SignalTargetRegistryState>(
          () => SignalTargetRegistryController(signalId),
          // Use the signalId as part of the cache name for Riverpod devtools
          name: 'SignalTargetRegistryController/$signalId',
        );

class SignalTargetRegistryController
    extends Notifier<SignalTargetRegistryState> {
  SignalTargetRegistryController(this._signalId);

  final String _signalId;

  SignalTargetRegistryRepository get _repository =>
      ref.read(signalTargetRegistryRepositoryProvider);

  @override
  SignalTargetRegistryState build() {
    Future.microtask(load);
    return const SignalTargetRegistryState(loading: true);
  }

  Future<void> load() async {
    state = const SignalTargetRegistryState(loading: true);
    try {
      final report = await _repository.fetchTargetRegistry(_signalId);
      state = SignalTargetRegistryState(report: report);
    } catch (_) {
      state = const SignalTargetRegistryState(
        errorCode: 'FAILED_TO_LOAD_TARGET_REGISTRY',
      );
    }
  }

  void reload() => load();
}

/// Provider for [SignalTargetRegistryRepository].
///
/// Overridden in the composition root (main.dart / test setup):
/// - [HttpSignalTargetRegistryRepository] in production
/// - [PreviewSignalTargetRegistryRepository] in preview builds and widget tests
final signalTargetRegistryRepositoryProvider =
    Provider<SignalTargetRegistryRepository>(
      (ref) => throw UnimplementedError(
        'signalTargetRegistryRepositoryProvider must be overridden '
        'in the composition root.',
      ),
    );