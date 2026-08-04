part of 'my_kefe_journey_screen.dart';

class _Journeys extends StatelessWidget {
  const _Journeys({required this.items, required this.strings});

  final List<MyKefeRecentJourney> items;
  final KefeStrings strings;

  @override
  Widget build(BuildContext context) {
    return KefeSurface(
      key: const ValueKey('my-kefe-recent-journeys'),
      tone: KefeSurfaceTone.raised,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          KefeEyebrow(strings.journeyRecent, icon: Icons.history_rounded),
          const SizedBox(height: 14),
          for (var i = 0; i < items.length; i++) ...[
            _ExpandableJourneyCard(item: items[i], strings: strings),
            if (i != items.length - 1) const SizedBox(height: 10),
          ],
        ],
      ),
    );
  }
}

class _ExpandableJourneyCard extends ConsumerWidget {
  const _ExpandableJourneyCard({required this.item, required this.strings});

  final MyKefeRecentJourney item;
  final KefeStrings strings;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final visual = context.kefeVisual;
    final locale = Localizations.localeOf(context);
    final localizer = ref.watch(kefeContentLocalizerProvider);
    final title = localizer.text(
      namespace: KefeContentNamespace.caseTitle,
      id: item.caseId,
      locale: locale,
      fallback: item.title,
    );
    return Theme(
      data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
      child: Container(
        decoration: BoxDecoration(
          color: visual.surfaceSunken,
          borderRadius: BorderRadius.circular(17),
          border: Border.all(color: visual.border),
        ),
        child: ExpansionTile(
          key: ValueKey('my-kefe-journey-detail-${item.caseId}'),
          tilePadding: const EdgeInsets.symmetric(horizontal: 13, vertical: 4),
          childrenPadding: const EdgeInsets.fromLTRB(13, 0, 13, 14),
          iconColor: visual.gold,
          collapsedIconColor: visual.mutedForeground,
          title: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                strings.domainName(item.primaryDomain),
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                  color: visual.gold,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 5),
              Text(
                title,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w800,
                ),
              ),
            ],
          ),
          subtitle: Padding(
            padding: const EdgeInsets.only(top: 9),
            child: Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                if (item.decisionUpdateCount > 0)
                  _JourneyPill(
                    label: strings.journeyUpdateCount(item.decisionUpdateCount),
                    color: visual.rules,
                  ),
                if (item.reflectionCompleted)
                  _JourneyPill(
                    label: strings.journeyReflected,
                    color: visual.gold,
                  ),
                _JourneyPill(
                  label: strings.journeyDetails,
                  color: visual.mutedForeground,
                ),
              ],
            ),
          ),
          children: [_JourneyTimeline(item: item, strings: strings)],
        ),
      ),
    );
  }
}

class _JourneyTimeline extends StatelessWidget {
  const _JourneyTimeline({required this.item, required this.strings});

  final MyKefeRecentJourney item;
  final KefeStrings strings;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final dates = MaterialLocalizations.of(context);
    String format(DateTime value) => dates.formatMediumDate(value.toLocal());
    return KefeSurface(
      key: const ValueKey('my-kefe-journey-timeline'),
      tone: KefeSurfaceTone.raised,
      accent: visual.rules,
      padding: const EdgeInsets.all(14),
      borderRadius: 15,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          KefeEyebrow(
            strings.journeyTimeline,
            icon: Icons.route_rounded,
            color: visual.rules,
          ),
          const SizedBox(height: 13),
          _JourneyTimelineItem(
            icon: Icons.lock_outline_rounded,
            color: visual.gold,
            title: strings.journeyInitialCommit,
            value: format(item.initialCommittedAt),
          ),
          const SizedBox(height: 12),
          _JourneyTimelineItem(
            icon: Icons.change_circle_outlined,
            color: visual.rules,
            title: item.decisionUpdateCount > 0
                ? strings.journeyUpdateCount(item.decisionUpdateCount)
                : strings.journeyNoUpdate,
            value: item.decisionUpdateCount > 0
                ? '${strings.journeyLatestDecision} · ${format(item.latestDecisionAt)}'
                : format(item.latestDecisionAt),
          ),
          const SizedBox(height: 12),
          _JourneyTimelineItem(
            icon: item.reflectionCompleted
                ? Icons.check_circle_outline_rounded
                : Icons.hourglass_empty_rounded,
            color: item.reflectionCompleted
                ? visual.success
                : visual.mutedForeground,
            title: item.reflectionCompleted
                ? strings.journeyReflected
                : strings.journeyReflectionPending,
            value: strings.journeyNonInferenceNote,
          ),
        ],
      ),
    );
  }
}

class _JourneyTimelineItem extends StatelessWidget {
  const _JourneyTimelineItem({
    required this.icon,
    required this.color,
    required this.title,
    required this.value,
  });

  final IconData icon;
  final Color color;
  final String title;
  final String value;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 34,
          height: 34,
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.10),
            shape: BoxShape.circle,
          ),
          child: Icon(icon, color: color, size: 18),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 3),
              Text(
                value,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: visual.mutedForeground,
                  height: 1.38,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
