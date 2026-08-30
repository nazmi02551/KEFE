part of 'my_kefe_journey_screen.dart';

class _Header extends StatelessWidget {
  const _Header({required this.strings});

  final KefeStrings strings;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return KefeSurface(
      tone: KefeSurfaceTone.premium,
      accent: visual.gold,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                KefeEyebrow(
                  strings.journeyEyebrow,
                  icon: Icons.timeline_rounded,
                ),
                const SizedBox(height: 9),
                Text(
                  strings.journeyTitle,
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    color: visual.onSurfaceStrong,
                    fontWeight: FontWeight.w900,
                    height: 1.08,
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  strings.journeySubtitle,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: visual.onSurfaceStrong.withValues(alpha: 0.76),
                    height: 1.45,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 14),
          Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              color: visual.gold.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: visual.goldSoft.withValues(alpha: 0.34),
              ),
            ),
            child: Icon(Icons.timeline_rounded, color: visual.goldSoft),
          ),
        ],
      ),
    );
  }
}

class _Overview extends StatelessWidget {
  const _Overview({
    required this.progress,
    required this.journey,
    required this.strings,
  });

  final MyKefeProgress progress;
  final MyKefeJourney journey;
  final KefeStrings strings;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return KefeSurface(
      tone: KefeSurfaceTone.premium,
      accent: visual.gold,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            strings.progressReadiness(progress.readiness),
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: visual.onSurfaceStrong.withValues(alpha: 0.82),
              height: 1.4,
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _Metric(
                  key: const ValueKey('my-kefe-weigh-count'),
                  value: progress.meaningfulWeighCount,
                  label: strings.progressWeighs,
                  icon: Icons.balance_rounded,
                  accent: visual.goldSoft,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _Metric(
                  key: const ValueKey('my-kefe-update-count'),
                  value: journey.decisionUpdateCount,
                  label: strings.journeyRevisits,
                  icon: Icons.change_circle_outlined,
                  accent: visual.rules,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _Metric(
                  key: const ValueKey('my-kefe-reflection-count'),
                  value: journey.reflectionCompletionCount,
                  label: strings.journeyReflections,
                  icon: Icons.auto_awesome_outlined,
                  accent: visual.empathy,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _NextStep extends StatelessWidget {
  const _NextStep({required this.journey, required this.strings});

  final MyKefeJourney journey;
  final KefeStrings strings;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final hasPendingReflection = journey.recentJourneys.any(
      (item) => !item.reflectionCompleted,
    );
    final title = hasPendingReflection
        ? strings.journeyNextReflectionTitle
        : journey.revisitedCaseCount == 0
        ? strings.journeyNextRevisitTitle
        : strings.journeyNextExploreTitle;
    final body = hasPendingReflection
        ? strings.journeyNextReflectionBody
        : journey.revisitedCaseCount == 0
        ? strings.journeyNextRevisitBody
        : strings.journeyNextExploreBody;

    return KefeSurface(
      key: const ValueKey('my-kefe-next-step'),
      tone: KefeSurfaceTone.raised,
      accent: visual.empathy,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          KefeEyebrow(
            strings.journeyNextEyebrow,
            icon: Icons.explore_outlined,
            color: visual.empathy,
          ),
          const SizedBox(height: 10),
          Text(
            title,
            key: const ValueKey('my-kefe-next-step-title'),
            style: Theme.of(
              context,
            ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 7),
          Text(
            body,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: visual.mutedForeground,
              height: 1.45,
            ),
          ),
          const SizedBox(height: 14),
          FilledButton.icon(
            key: const ValueKey('my-kefe-next-step-action'),
            onPressed: () => context.go('/explore'),
            icon: const Icon(Icons.arrow_forward_rounded),
            label: Text(strings.journeyNextAction),
          ),
        ],
      ),
    );
  }
}

class _ReportEntry extends StatelessWidget {
  const _ReportEntry({required this.momentCount, required this.strings});

  final int momentCount;
  final KefeStrings strings;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return KefeSurface(
      key: const ValueKey('my-kefe-report-entry'),
      tone: KefeSurfaceTone.premium,
      accent: visual.rules,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          KefeEyebrow(
            strings.reportEntryEyebrow,
            icon: Icons.route_rounded,
            color: visual.rules,
          ),
          const SizedBox(height: 10),
          Text(
            strings.reportEntryTitle,
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              color: visual.onSurfaceStrong,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            strings.reportEntryBody,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: visual.onSurfaceStrong.withValues(alpha: 0.76),
              height: 1.45,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            strings.reportEntryCount(momentCount),
            key: const ValueKey('my-kefe-report-moment-count'),
            style: Theme.of(context).textTheme.labelLarge?.copyWith(
              color: visual.goldSoft,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 14),
          FilledButton.icon(
            key: const ValueKey('my-kefe-report-action'),
            onPressed: () => context.push('/my-kefe/report'),
            icon: const Icon(Icons.arrow_forward_rounded),
            label: Text(strings.reportEntryAction),
          ),
        ],
      ),
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric({
    required this.value,
    required this.label,
    required this.icon,
    required this.accent,
    super.key,
  });

  final int value;
  final String label;
  final IconData icon;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Semantics(
      label: '$label: $value',
      child: Container(
        constraints: const BoxConstraints(minHeight: 108),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 11),
        decoration: BoxDecoration(
          color: visual.onSurfaceStrong.withValues(alpha: 0.06),
          borderRadius: BorderRadius.circular(17),
          border: Border.all(
            color: visual.onSurfaceStrong.withValues(alpha: 0.12),
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 18, color: accent),
            const SizedBox(height: 7),
            Text(
              '$value',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                color: visual.onSurfaceStrong,
                fontWeight: FontWeight.w900,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              maxLines: 2,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: visual.onSurfaceStrong.withValues(alpha: 0.70),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Domains extends StatelessWidget {
  const _Domains({required this.items, required this.strings});

  final List<MyKefeDomainActivity> items;
  final KefeStrings strings;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final max = items.fold<int>(
      1,
      (m, e) => e.committedWeighCount > m ? e.committedWeighCount : m,
    );
    return KefeSurface(
      key: const ValueKey('my-kefe-domain-activity'),
      tone: KefeSurfaceTone.raised,
      accent: visual.rules,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          KefeEyebrow(
            strings.journeyDomainActivity,
            icon: Icons.grid_view_rounded,
            color: visual.rules,
          ),
          const SizedBox(height: 16),
          for (var i = 0; i < items.length; i++) ...[
            Row(
              children: [
                Expanded(
                  child: Text(
                    strings.domainName(items[i].primaryDomain),
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                Text(
                  strings.journeyWeighCount(items[i].committedWeighCount),
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: visual.mutedForeground,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 7),
            ClipRRect(
              borderRadius: BorderRadius.circular(999),
              child: LinearProgressIndicator(
                value: items[i].committedWeighCount / max,
                minHeight: 7,
                color: visual.rules,
                backgroundColor: visual.surfaceSunken,
              ),
            ),
            if (i != items.length - 1) const SizedBox(height: 14),
          ],
        ],
      ),
    );
  }
}
