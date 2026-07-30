import 'package:flutter/material.dart';

import '../../core/design/kefe_surface.dart';
import '../../core/design/kefe_visual_system.dart';

class PreviewPageHeader extends StatelessWidget {
  const PreviewPageHeader({
    required this.eyebrow,
    required this.title,
    required this.icon,
    super.key,
  });

  final String eyebrow;
  final String title;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              KefeEyebrow(eyebrow, color: visual.goldSoft),
              const SizedBox(height: 8),
              Text(
                title,
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.w900,
                  height: 1.08,
                ),
              ),
            ],
          ),
        ),
        Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            color: visual.subtleGoldSurface,
            shape: BoxShape.circle,
            border: Border.all(color: visual.gold.withValues(alpha: 0.26)),
            boxShadow: [
              BoxShadow(
                color: visual.gold.withValues(
                  alpha: visual.isDark ? 0.08 : 0.05,
                ),
                blurRadius: 18,
              ),
            ],
          ),
          child: Icon(icon, color: visual.goldSoft),
        ),
      ],
    );
  }
}

class PreviewNotice extends StatelessWidget {
  const PreviewNotice({required this.text, super.key});

  final String text;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Semantics(
      container: true,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 11),
        decoration: BoxDecoration(
          color: visual.subtleRulesSurface,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: visual.rules.withValues(alpha: 0.24)),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.visibility_outlined, color: visual.rules, size: 18),
            const SizedBox(width: 9),
            Expanded(
              child: Text(
                text,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: visual.mutedForeground,
                  height: 1.35,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class PreviewFilterPill extends StatelessWidget {
  const PreviewFilterPill({
    required this.label,
    this.selected = false,
    super.key,
  });

  final String label;
  final bool selected;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Semantics(
      selected: selected,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: selected ? visual.gold : visual.surfaceSunken,
          borderRadius: BorderRadius.circular(99),
          border: Border.all(
            color: selected
                ? visual.gold
                : visual.border.withValues(alpha: 0.90),
          ),
        ),
        child: Text(
          label,
          style: Theme.of(context).textTheme.labelMedium?.copyWith(
            color: selected ? visual.surfaceStrong : visual.foreground,
            fontWeight: FontWeight.w800,
          ),
        ),
      ),
    );
  }
}

class PreviewScoreOrb extends StatelessWidget {
  const PreviewScoreOrb({
    required this.label,
    required this.value,
    required this.color,
    super.key,
  });

  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) => Column(
    children: [
      Text(
        label,
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
          color: color,
          fontWeight: FontWeight.w700,
        ),
      ),
      const SizedBox(height: 5),
      Container(
        width: 58,
        height: 58,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: color.withValues(alpha: 0.10),
          border: Border.all(color: color.withValues(alpha: 0.45)),
        ),
        child: Text(
          value,
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
            color: color,
            fontWeight: FontWeight.w900,
          ),
        ),
      ),
    ],
  );
}

class PreviewActionCaseCard extends StatelessWidget {
  const PreviewActionCaseCard({
    required this.label,
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.onTap,
    super.key,
  });

  final String label;
  final String title;
  final String subtitle;
  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Semantics(
      button: true,
      label: title,
      child: KefeSurface(
        padding: EdgeInsets.zero,
        tone: KefeSurfaceTone.raised,
        child: InkWell(
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.all(17),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: visual.subtleGoldSurface,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(
                      color: visual.gold.withValues(alpha: 0.20),
                    ),
                  ),
                  child: Icon(icon, color: visual.goldSoft),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        label,
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: visual.goldSoft,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        title,
                        style: Theme.of(context).textTheme.titleMedium
                            ?.copyWith(
                              fontWeight: FontWeight.w800,
                              height: 1.2,
                            ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        subtitle,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: visual.mutedForeground,
                          height: 1.35,
                        ),
                      ),
                    ],
                  ),
                ),
                Icon(
                  Icons.chevron_right_rounded,
                  color: visual.mutedForeground,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
