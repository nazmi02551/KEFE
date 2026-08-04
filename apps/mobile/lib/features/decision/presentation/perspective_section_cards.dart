part of 'perspective_section.dart';

class _MethodNote extends StatelessWidget {
  const _MethodNote({
    required this.icon,
    required this.text,
    required this.accent,
    super.key,
  });

  final IconData icon;
  final String text;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: accent.withValues(alpha: visual.isDark ? 0.10 : 0.07),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: accent.withValues(alpha: 0.22)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18, color: accent),
          const SizedBox(width: 9),
          Expanded(
            child: Text(
              text,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: visual.mutedForeground,
                height: 1.4,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _PerspectiveCardView extends StatelessWidget {
  const _PerspectiveCardView({
    required this.card,
    required this.body,
    required this.provenance,
  });

  final PerspectiveCard card;
  final String body;
  final String provenance;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final theme = context.kefeVisual;
    final visual = _slotVisual(theme, card.slot);
    final label = strings.perspectiveSlotLabel(card.slot);

    return Semantics(
      container: true,
      label: label,
      child: Container(
        key: ValueKey('perspective-card-${card.slot.name}'),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              theme.surfaceRaised,
              visual.color.withValues(alpha: theme.isDark ? 0.10 : 0.055),
            ],
          ),
          border: Border.all(color: visual.color.withValues(alpha: 0.28)),
          borderRadius: BorderRadius.circular(18),
          boxShadow: [
            BoxShadow(
              color: visual.color.withValues(
                alpha: theme.isDark ? 0.06 : 0.035,
              ),
              blurRadius: 20,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Container(
                  width: 34,
                  height: 34,
                  decoration: BoxDecoration(
                    color: visual.color.withValues(alpha: 0.13),
                    borderRadius: BorderRadius.circular(11),
                    border: Border.all(
                      color: visual.color.withValues(alpha: 0.22),
                    ),
                  ),
                  child: Icon(visual.icon, size: 18, color: visual.color),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    label,
                    style: Theme.of(context).textTheme.labelLarge?.copyWith(
                      color: visual.color,
                      fontWeight: FontWeight.w900,
                      letterSpacing: 0.2,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 13),
            Text(
              body,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                height: 1.5,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 13),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              decoration: BoxDecoration(
                color: theme.surfaceSunken.withValues(alpha: 0.72),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: theme.border.withValues(alpha: 0.78)),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(
                    Icons.source_outlined,
                    size: 16,
                    color: theme.mutedForeground,
                  ),
                  const SizedBox(width: 7),
                  Expanded(
                    child: Text(
                      '${strings.perspectiveSourceLabel(card.sourceKind)} · $provenance',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: theme.mutedForeground,
                        height: 1.35,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _MethodologyPill extends StatelessWidget {
  const _MethodologyPill({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      decoration: BoxDecoration(
        color: visual.subtleGoldSurface,
        borderRadius: BorderRadius.circular(99),
        border: Border.all(color: visual.gold.withValues(alpha: 0.20)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: visual.goldSoft),
          const SizedBox(width: 6),
          Text(
            label,
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: visual.mutedForeground,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}

({Color color, IconData icon}) _slotVisual(
  KefeVisualTheme visual,
  PerspectiveSlot slot,
) => switch (slot) {
  PerspectiveSlot.near => (color: visual.success, icon: Icons.near_me_outlined),
  PerspectiveSlot.opposing => (
    color: visual.empathy,
    icon: Icons.swap_horiz_rounded,
  ),
  PerspectiveSlot.bridge => (color: visual.gold, icon: Icons.hub_outlined),
  PerspectiveSlot.alternativeContext => (
    color: visual.rules,
    icon: Icons.change_circle_outlined,
  ),
};
