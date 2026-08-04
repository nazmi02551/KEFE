part of 'my_kefe_journey_screen.dart';

class _LegacyRecent extends ConsumerWidget {
  const _LegacyRecent({required this.progress, required this.strings});

  final MyKefeProgress progress;
  final KefeStrings strings;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final visual = context.kefeVisual;
    final locale = Localizations.localeOf(context);
    final localizer = ref.watch(kefeContentLocalizerProvider);
    return KefeSurface(
      tone: KefeSurfaceTone.raised,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          KefeEyebrow(strings.progressRecent, icon: Icons.history_rounded),
          const SizedBox(height: 12),
          for (final item in progress.recentCases)
            Padding(
              padding: const EdgeInsets.only(bottom: 9),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 7,
                    height: 7,
                    margin: const EdgeInsets.only(top: 6),
                    decoration: BoxDecoration(
                      color: visual.gold,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      '${localizer.text(namespace: KefeContentNamespace.caseTitle, id: item.caseId, locale: locale, fallback: item.title)} · ${strings.domainName(item.primaryDomain)}',
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

class _JourneyPill extends StatelessWidget {
  const _JourneyPill({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
    decoration: BoxDecoration(
      color: color.withValues(alpha: 0.10),
      borderRadius: BorderRadius.circular(999),
      border: Border.all(color: color.withValues(alpha: 0.20)),
    ),
    child: Text(
      label,
      style: Theme.of(context).textTheme.labelSmall?.copyWith(
        color: color,
        fontWeight: FontWeight.w800,
      ),
    ),
  );
}

class _Notice extends StatelessWidget {
  const _Notice({required this.text, super.key});

  final String text;

  @override
  Widget build(BuildContext context) => KefeSurface(
    padding: const EdgeInsets.all(13),
    tone: KefeSurfaceTone.sunken,
    accent: context.kefeVisual.rules,
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(Icons.science_outlined, size: 18, color: context.kefeVisual.rules),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            text,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: context.kefeVisual.mutedForeground,
              height: 1.4,
            ),
          ),
        ),
      ],
    ),
  );
}

class _Footnote extends StatelessWidget {
  const _Footnote({required this.strings});

  final KefeStrings strings;

  @override
  Widget build(BuildContext context) => KefeSurface(
    key: const ValueKey('my-kefe-no-inference-note'),
    tone: KefeSurfaceTone.sunken,
    padding: const EdgeInsets.all(15),
    accent: context.kefeVisual.gold,
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(
          Icons.visibility_outlined,
          size: 18,
          color: context.kefeVisual.gold,
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            strings.journeyNonInferenceNote,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: context.kefeVisual.mutedForeground,
              height: 1.4,
            ),
          ),
        ),
      ],
    ),
  );
}
