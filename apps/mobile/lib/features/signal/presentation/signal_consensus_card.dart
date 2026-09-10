import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/signal_consensus_card_models.dart';

class SignalConsensusCard extends StatelessWidget {
  const SignalConsensusCard({
    required this.signal,
    this.onTap,
    super.key,
  });

  final SignalConsensusCardModel signal;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _tierColor(visual, signal.confidenceTier);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('signal-consensus-${signal.signalId}'),
        tone: KefeSurfaceTone.raised,
        padding: const EdgeInsets.all(18),
        borderRadius: 22,
        accent: accent,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (signal.isProvisional) ...[
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: visual.attention.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(
                    color: visual.attention.withValues(alpha: 0.4),
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.hourglass_top_rounded,
                      size: 12,
                      color: visual.attention,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      strings.signalCardProvisionalLabel,
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                        color: visual.attention,
                        letterSpacing: 0.2,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 8),
            ],
            Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: accent.withValues(alpha: visual.isDark ? 0.18 : 0.10),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: accent.withValues(alpha: 0.3)),
                  ),
                  child: Icon(Icons.workspace_premium_rounded, color: accent, size: 20),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.signalCardEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _tierLabel(strings, signal.confidenceTier),
                        style: TextStyle(
                          fontSize: 11.5,
                          fontWeight: FontWeight.w800,
                          color: accent,
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
                  decoration: BoxDecoration(
                    color: visual.surfaceSunken,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: visual.border.withValues(alpha: 0.6)),
                  ),
                  child: Text(
                    strings.signalCardAgreementBadge(
                      signal.agreementPercentage.round(),
                      signal.sampleSize,
                    ),
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.w800,
                      color: visual.foreground,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              signal.caseTitle,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w900,
                letterSpacing: -0.2,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              signal.consensusStatement,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                height: 1.4,
                color: visual.mutedForeground,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _tierColor(KefeVisualTheme visual, SignalConfidenceTierModel tier) =>
      switch (tier) {
        SignalConfidenceTierModel.gold => visual.gold,
        SignalConfidenceTierModel.silver => visual.rules,
        SignalConfidenceTierModel.bronze => visual.attention,
      };

  String _tierLabel(KefeStrings strings, SignalConfidenceTierModel tier) =>
      switch (tier) {
        SignalConfidenceTierModel.gold => strings.signalCardTierGold,
        SignalConfidenceTierModel.silver => strings.signalCardTierSilver,
        SignalConfidenceTierModel.bronze => strings.signalCardTierBronze,
      };
}
