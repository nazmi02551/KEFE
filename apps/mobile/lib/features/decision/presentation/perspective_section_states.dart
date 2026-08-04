part of 'perspective_section.dart';

class _PerspectiveHeader extends StatelessWidget {
  const _PerspectiveHeader({required this.strings});

  final KefeStrings strings;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            color: visual.subtleRulesSurface,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: visual.rules.withValues(alpha: 0.22)),
          ),
          child: Icon(Icons.forum_outlined, color: visual.rules),
        ),
        const SizedBox(width: 13),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              KefeEyebrow(strings.perspectiveEyebrow, color: visual.rules),
              const SizedBox(height: 4),
              Text(
                strings.perspectiveTitle,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w900,
                  height: 1.15,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _LoadingState extends StatelessWidget {
  const _LoadingState({required this.strings});

  final KefeStrings strings;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Semantics(
      label: strings.perspectiveLoading,
      liveRegion: true,
      child: KefeSurface(
        key: const ValueKey('perspective-loading'),
        tone: KefeSurfaceTone.sunken,
        accent: visual.rules,
        padding: const EdgeInsets.all(14),
        borderRadius: 17,
        child: Row(
          children: [
            ExcludeSemantics(
              child: Icon(
                Icons.hourglass_top_rounded,
                color: visual.rules,
                size: 21,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                strings.perspectiveLoading,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: visual.foreground,
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

class _RetryState extends StatelessWidget {
  const _RetryState({required this.strings, required this.onRetry});

  final KefeStrings strings;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Semantics(
      liveRegion: true,
      child: KefeSurface(
        key: const ValueKey('perspective-error'),
        tone: KefeSurfaceTone.sunken,
        accent: visual.empathy,
        padding: const EdgeInsets.all(14),
        borderRadius: 17,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                ExcludeSemantics(
                  child: Icon(
                    Icons.error_outline_rounded,
                    color: visual.empathy,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    strings.perspectiveUnavailable,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: visual.foreground,
                      height: 1.4,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              key: const ValueKey('perspective-retry'),
              onPressed: onRetry,
              icon: const Icon(Icons.refresh_rounded),
              label: Text(strings.perspectiveRetry),
            ),
          ],
        ),
      ),
    );
  }
}

class _UnavailableState extends StatelessWidget {
  const _UnavailableState({required this.strings});

  final KefeStrings strings;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Semantics(
      liveRegion: true,
      child: KefeSurface(
        key: const ValueKey('perspective-unavailable'),
        tone: KefeSurfaceTone.sunken,
        accent: visual.empathy,
        padding: const EdgeInsets.all(14),
        borderRadius: 17,
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ExcludeSemantics(
              child: Icon(Icons.info_outline_rounded, color: visual.empathy),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                strings.perspectiveUnavailable,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: visual.foreground,
                  height: 1.4,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
