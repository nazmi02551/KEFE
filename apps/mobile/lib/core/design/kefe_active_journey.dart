import 'package:flutter/material.dart';

import 'kefe_surface.dart';
import 'kefe_visual_system.dart';

class KefeActiveJourney extends StatelessWidget {
  const KefeActiveJourney({
    required this.stageId,
    required this.eyebrow,
    required this.title,
    required this.progressLabel,
    required this.child,
    this.icon = Icons.route_rounded,
    this.subtitle,
    super.key,
  });

  final String stageId;
  final String eyebrow;
  final String title;
  final String progressLabel;
  final Widget child;
  final IconData icon;
  final String? subtitle;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Semantics(
      key: const ValueKey('kefe-active-journey'),
      container: true,
      label: '$eyebrow. $title. $progressLabel',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          KefeSurface(
            tone: KefeSurfaceTone.premium,
            accent: visual.gold,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            borderRadius: 22,
            child: Row(
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
                    child: Icon(icon, color: visual.goldSoft, size: 22),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(eyebrow, color: visual.goldSoft),
                      const SizedBox(height: 5),
                      Text(
                        title,
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          color: visual.onSurfaceStrong,
                          fontWeight: FontWeight.w900,
                          height: 1.16,
                        ),
                      ),
                      if (subtitle != null) ...[
                        const SizedBox(height: 6),
                        Text(
                          subtitle!,
                          style: Theme.of(context).textTheme.bodySmall
                              ?.copyWith(
                                color: visual.onSurfaceStrong.withValues(
                                  alpha: 0.72,
                                ),
                                height: 1.4,
                              ),
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(width: 10),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 9,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: visual.gold.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(99),
                    border: Border.all(
                      color: visual.gold.withValues(alpha: 0.28),
                    ),
                  ),
                  child: Text(
                    progressLabel,
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: visual.goldSoft,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
          AnimatedSwitcher(
            duration: KefeMotion.resolve(
              context,
              const Duration(milliseconds: 220),
            ),
            switchInCurve: Curves.easeOutCubic,
            switchOutCurve: Curves.easeInCubic,
            child: KeyedSubtree(key: ValueKey(stageId), child: child),
          ),
        ],
      ),
    );
  }
}
