import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/bridge_argument_models.dart';

class BridgeArgumentCard extends StatelessWidget {
  const BridgeArgumentCard({
    required this.bridge,
    super.key,
  });

  final BridgeArgumentItemModel bridge;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = visual.gold;

    return KefeSurface(
      key: ValueKey('bridge-argument-${bridge.id}'),
      tone: KefeSurfaceTone.raised,
      padding: const EdgeInsets.all(18),
      borderRadius: 22,
      accent: accent,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: accent.withValues(alpha: visual.isDark ? 0.16 : 0.08),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: accent.withValues(alpha: 0.25)),
                ),
                child: Icon(Icons.hub_outlined, color: accent, size: 18),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    KefeEyebrow(strings.bridgeEyebrow, color: accent),
                    const SizedBox(height: 2),
                    Text(
                      strings.bridgeCrossSupport(
                        (bridge.crossGroupSupportRate * 100).round(),
                        bridge.sampleSize,
                      ),
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: visual.mutedForeground,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            bridge.synthesisThesis,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              height: 1.45,
              fontWeight: FontWeight.w600,
              color: visual.foreground,
            ),
          ),
          if (bridge.connectingValues.isNotEmpty) ...[
            const SizedBox(height: 12),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: bridge.connectingValues.map((val) {
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: visual.surfaceSunken,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: visual.border.withValues(alpha: 0.6)),
                  ),
                  child: Text(
                    '#$val',
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.w700,
                      color: visual.goldSoft,
                    ),
                  ),
                );
              }).toList(),
            ),
          ],
        ],
      ),
    );
  }
}
