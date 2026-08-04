part of 'perspective_section.dart';

class PerspectiveSection extends ConsumerWidget {
  const PerspectiveSection({
    required this.state,
    required this.result,
    required this.reasonPendingModeration,
    required this.onRetry,
    this.includePostCommitCapabilities = true,
    super.key,
  });

  final PerspectiveUiState state;
  final PerspectiveResult? result;
  final bool reasonPendingModeration;
  final VoidCallback onRetry;
  final bool includePostCommitCapabilities;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final decision = ref.watch(decisionControllerProvider);
    final sessionId = decision.sessionId;
    final caseVersionId = decision.caseData?.versionId;
    final hasCommittedContext =
        decision.reveal != null && sessionId != null && caseVersionId != null;
    final consensus = includePostCommitCapabilities && hasCommittedContext
        ? ConsensusSection(sessionId: sessionId, caseVersionId: caseVersionId)
        : null;
    final community = includePostCommitCapabilities && hasCommittedContext
        ? CommunityReasonSection(
            sessionId: sessionId,
            caseVersionId: caseVersionId,
          )
        : null;
    final share = includePostCommitCapabilities && hasCommittedContext
        ? ShareSection(sessionId: sessionId)
        : null;

    if (state == PerspectiveUiState.idle) {
      if (!hasCommittedContext) return const SizedBox.shrink();
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          ?consensus,
          if (community != null) ...[const SizedBox(height: 20), community],
          if (share != null) ...[const SizedBox(height: 20), share],
        ],
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        KefeSurface(
          key: const ValueKey('perspective-section'),
          tone: KefeSurfaceTone.raised,
          accent: visual.rules,
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _PerspectiveHeader(strings: strings),
              if (reasonPendingModeration) ...[
                const SizedBox(height: 14),
                Semantics(
                  liveRegion: true,
                  child: _MethodNote(
                    key: const ValueKey('reason-pending-moderation'),
                    icon: Icons.shield_outlined,
                    text: strings.reasonPendingModeration,
                    accent: visual.attention,
                  ),
                ),
              ],
              const SizedBox(height: 18),
              switch (state) {
                PerspectiveUiState.loading => _LoadingState(strings: strings),
                PerspectiveUiState.errorRetryable => _RetryState(
                  strings: strings,
                  onRetry: onRetry,
                ),
                PerspectiveUiState.ready ||
                PerspectiveUiState.clusterPending ||
                PerspectiveUiState.degradedCurated => _LoadedState(
                  state: state,
                  result: result,
                ),
                PerspectiveUiState.idle => const SizedBox.shrink(),
              },
            ],
          ),
        ),
        if (consensus != null) ...[const SizedBox(height: 20), consensus],
        if (community != null) ...[const SizedBox(height: 20), community],
        if (includePostCommitCapabilities) ...[
          const SizedBox(height: 20),
          const ProgressSection(),
        ],
        if (share != null) ...[const SizedBox(height: 20), share],
      ],
    );
  }
}
