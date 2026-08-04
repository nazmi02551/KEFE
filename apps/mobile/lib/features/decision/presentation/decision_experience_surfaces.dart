part of 'decision_experience_screen.dart';

class _JourneyCaseHeader extends StatelessWidget {
  const _JourneyCaseHeader({required this.caseData});

  final DecisionCase caseData;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return KefeSurface(
      key: const ValueKey('production-case-summary-header'),
      tone: KefeSurfaceTone.premium,
      padding: const EdgeInsets.all(20),
      borderRadius: 26,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: visual.subtleGoldSurface,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(
                    color: visual.gold.withValues(alpha: 0.28),
                  ),
                ),
                child: ExcludeSemantics(
                  child: Icon(
                    Icons.balance_rounded,
                    color: visual.goldSoft,
                    size: 24,
                  ),
                ),
              ),
              const SizedBox(width: 13),
              Expanded(
                child: Text(
                  caseData.title,
                  key: const ValueKey('case-title'),
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    color: visual.onSurfaceStrong,
                    fontWeight: FontWeight.w900,
                    height: 1.14,
                    letterSpacing: -0.35,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Text(
            caseData.summary,
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: visual.onSurfaceStrong.withValues(alpha: 0.74),
              height: 1.46,
            ),
          ),
        ],
      ),
    );
  }
}

class _ContextAdvancePanel extends StatelessWidget {
  const _ContextAdvancePanel({required this.enabled, required this.onContinue});

  final bool enabled;
  final VoidCallback onContinue;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    return KefeSurface(
      key: const ValueKey('context-advance-panel'),
      tone: KefeSurfaceTone.raised,
      accent: visual.rules,
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            strings.contextAdvanceHelper,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: visual.mutedForeground,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 12),
          FilledButton.icon(
            key: const ValueKey('context-continue-button'),
            onPressed: enabled ? onContinue : null,
            icon: const Icon(Icons.arrow_forward_rounded),
            label: Text(strings.contextAdvanceAction),
          ),
        ],
      ),
    );
  }
}

class _JourneyCommitPanel extends StatelessWidget {
  const _JourneyCommitPanel({
    required this.onPressed,
    required this.submitting,
    required this.recoveryPending,
    required this.hasRequiredResponses,
  });

  final VoidCallback? onPressed;
  final bool submitting;
  final bool recoveryPending;
  final bool hasRequiredResponses;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final helper = !hasRequiredResponses
        ? strings.completeRequired
        : recoveryPending
        ? strings.pendingHelper
        : strings.commitHelper;
    final buttonLabel = submitting
        ? strings.loading
        : recoveryPending
        ? strings.retrySync
        : strings.commit;

    return KefeSurface(
      key: const ValueKey('commit-action-panel'),
      tone: KefeSurfaceTone.raised,
      accent: recoveryPending ? visual.attention : visual.gold,
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Semantics(
            liveRegion: submitting,
            child: FilledButton.icon(
              key: const ValueKey('commit-button'),
              onPressed: onPressed,
              icon: Icon(
                submitting
                    ? Icons.hourglass_top_rounded
                    : recoveryPending
                    ? Icons.sync_rounded
                    : Icons.lock_rounded,
              ),
              label: Text(buttonLabel),
            ),
          ),
          const SizedBox(height: 10),
          Text(
            helper,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: visual.mutedForeground,
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }
}

class _JourneyStatusSurface extends StatelessWidget {
  const _JourneyStatusSurface({
    required this.message,
    required this.offlineDraft,
  });

  final String message;
  final bool offlineDraft;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final accent = offlineDraft
        ? visual.attention
        : Theme.of(context).colorScheme.error;
    return Semantics(
      liveRegion: true,
      child: KefeSurface(
        tone: KefeSurfaceTone.sunken,
        accent: accent,
        padding: const EdgeInsets.all(15),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ExcludeSemantics(
              child: Icon(
                offlineDraft
                    ? Icons.cloud_off_rounded
                    : Icons.error_outline_rounded,
                color: accent,
                size: 21,
              ),
            ),
            const SizedBox(width: 11),
            Expanded(
              child: Text(
                message,
                key: const ValueKey('decision-status-message'),
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: visual.foreground,
                  height: 1.42,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _JourneyMessageSurface extends StatelessWidget {
  const _JourneyMessageSurface({required this.message, super.key});

  final String message;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return KefeSurface(
      tone: KefeSurfaceTone.raised,
      accent: visual.attention,
      padding: const EdgeInsets.all(18),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ExcludeSemantics(
            child: Icon(Icons.info_outline_rounded, color: visual.attention),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              message,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: visual.foreground,
                height: 1.42,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _JourneyLoadingState extends StatelessWidget {
  const _JourneyLoadingState({required this.label, super.key});

  final String label;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: KefeSurface(
          tone: KefeSurfaceTone.raised,
          accent: visual.gold,
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
          child: Semantics(
            liveRegion: true,
            label: label,
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.hourglass_top_rounded, color: visual.goldSoft),
                const SizedBox(width: 12),
                Flexible(
                  child: Text(
                    label,
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _JourneyErrorState extends StatelessWidget {
  const _JourneyErrorState({
    required this.message,
    required this.retryLabel,
    required this.onRetry,
    super.key,
  });

  final String message;
  final String retryLabel;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: KefeSurface(
          tone: KefeSurfaceTone.raised,
          accent: Theme.of(context).colorScheme.error,
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Icon(
                Icons.error_outline_rounded,
                color: Theme.of(context).colorScheme.error,
                size: 30,
              ),
              const SizedBox(height: 12),
              Text(
                message,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  color: visual.foreground,
                  height: 1.42,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 16),
              FilledButton(onPressed: onRetry, child: Text(retryLabel)),
            ],
          ),
        ),
      ),
    );
  }
}

class _JourneyFirstUseCompletion extends StatelessWidget {
  const _JourneyFirstUseCompletion({required this.onContinue});

  final VoidCallback onContinue;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    return KefeSurface(
      key: const ValueKey('first-use-completion'),
      tone: KefeSurfaceTone.premium,
      accent: visual.success,
      padding: const EdgeInsets.all(20),
      borderRadius: 24,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Icon(Icons.check_rounded, color: visual.success, size: 28),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  strings.firstRevealHelper,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: visual.onSurfaceStrong,
                    fontWeight: FontWeight.w800,
                    height: 1.35,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 18),
          FilledButton.icon(
            key: const ValueKey('continue-as-guest'),
            onPressed: onContinue,
            icon: const Icon(Icons.arrow_forward_rounded),
            label: Text(strings.continueAsGuest),
          ),
        ],
      ),
    );
  }
}
