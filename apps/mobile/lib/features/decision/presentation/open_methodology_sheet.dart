import 'package:flutter/material.dart';

import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/decision_models.dart';

class OpenMethodologySheet extends StatelessWidget {
  const OpenMethodologySheet({
    required this.reveal,
    super.key,
  });

  final RevealResult reveal;

  static Future<void> show(BuildContext context, RevealResult reveal) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => OpenMethodologySheet(reveal: reveal),
    );
  }

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;

    return Container(
      key: const ValueKey('open-methodology-sheet'),
      decoration: BoxDecoration(
        color: visual.surfaceRaised,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
        border: Border.all(color: visual.border.withValues(alpha: 0.8)),
      ),
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 16,
        bottom: MediaQuery.paddingOf(context).bottom + 20,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Center(
            child: Container(
              width: 36,
              height: 4,
              decoration: BoxDecoration(
                color: visual.mutedForeground.withValues(alpha: 0.35),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 18),
          Row(
            children: [
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  color: visual.subtleGoldSurface,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: visual.gold.withValues(alpha: 0.25)),
                ),
                child: Icon(
                  Icons.verified_user_outlined,
                  color: visual.gold,
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      strings.methodologySheetTitle,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w900,
                        letterSpacing: -0.2,
                      ),
                    ),
                    Text(
                      strings.methodologyEngine('v1.0'),
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: visual.mutedForeground,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              Expanded(
                child: _MetricBadge(
                  label: strings.methodologySampleLabel,
                  value: 'n=${reveal.sampleSize}',
                  icon: Icons.groups_2_outlined,
                  color: visual.rules,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _MetricBadge(
                  label: strings.methodologyConfidenceLabel,
                  value: strings.confidenceLabel(reveal.confidence),
                  icon: Icons.shield_outlined,
                  color: visual.gold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 22),
          Text(
            strings.methodologySafeguardsTitle,
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
              color: visual.mutedForeground,
              fontWeight: FontWeight.w900,
              letterSpacing: 0.8,
            ),
          ),
          const SizedBox(height: 12),
          _SafeguardRow(
            icon: Icons.lock_clock_outlined,
            text: strings.methodologySafeguardCommitFirst,
            color: visual.rules,
          ),
          const SizedBox(height: 10),
          _SafeguardRow(
            icon: Icons.filter_alt_outlined,
            text: strings.methodologySafeguardAntiSybil,
            color: visual.empathy,
          ),
          const SizedBox(height: 10),
          _SafeguardRow(
            icon: Icons.psychology_alt_outlined,
            text: strings.methodologySafeguardNoProfiling,
            color: visual.gold,
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            key: const ValueKey('methodology-close-button'),
            onPressed: () => Navigator.of(context).pop(),
            style: ElevatedButton.styleFrom(
              backgroundColor: visual.surfaceSunken,
              foregroundColor: visual.foreground,
              elevation: 0,
              padding: const EdgeInsets.symmetric(vertical: 14),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(14),
                side: BorderSide(color: visual.border),
              ),
            ),
            child: Text(
              strings.methodologyClose,
              style: const TextStyle(fontWeight: FontWeight.w800),
            ),
          ),
        ],
      ),
    );
  }
}

class _MetricBadge extends StatelessWidget {
  const _MetricBadge({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
  });

  final String label;
  final String value;
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: visual.surfaceSunken,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: visual.border.withValues(alpha: 0.6)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 14, color: color),
              const SizedBox(width: 5),
              Expanded(
                child: Text(
                  label,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 10.5,
                    color: visual.mutedForeground,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            value,
            style: TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w900,
              color: visual.foreground,
            ),
          ),
        ],
      ),
    );
  }
}

class _SafeguardRow extends StatelessWidget {
  const _SafeguardRow({
    required this.icon,
    required this.text,
    required this.color,
  });

  final IconData icon;
  final String text;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: visual.surfaceSunken.withValues(alpha: 0.5),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: visual.border.withValues(alpha: 0.4)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 16, color: color),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              text,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                height: 1.30,
                color: visual.foreground,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
