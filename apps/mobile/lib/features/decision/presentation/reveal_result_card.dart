import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_content_localizer.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../../core/localization/result_methodology_strings.dart';
import '../domain/decision_models.dart';

class RevealResultCard extends ConsumerWidget {
  const RevealResultCard({
    required this.reveal,
    required this.selectedOption,
    super.key,
  });

  final RevealResult reveal;
  final String? selectedOption;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final content = ref.watch(kefeContentLocalizerProvider);
    final entries = reveal.values.entries.toList(growable: false);
    final selectedShare = selectedOption == null
        ? null
        : reveal.values[selectedOption];
    final topEntry = entries.isEmpty
        ? null
        : entries.reduce((a, b) => a.value >= b.value ? a : b);
    final gapPoints = selectedShare == null || topEntry == null
        ? null
        : ((topEntry.value - selectedShare).abs() * 100).round();
    final showGapInsight = reveal.layer == 'TRUSTED';

    String optionLabel(String raw) => content.text(
      namespace: KefeContentNamespace.option,
      id: raw,
      locale: strings.locale,
      fallback: raw,
    );

    return KefeSurface(
      key: const ValueKey('reveal-card'),
      tone: KefeSurfaceTone.raised,
      padding: const EdgeInsets.all(20),
      borderRadius: 26,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _RevealHeader(strings: strings),
          if (selectedOption != null) ...[
            const SizedBox(height: 18),
            _PersonalDecision(
              label: optionLabel(selectedOption!),
              accent: _accentForRawOption(visual, entries, selectedOption!),
            ),
          ],
          const SizedBox(height: 22),
          Row(
            children: [
              Expanded(
                child: Text(
                  strings.communityDistribution,
                  style: Theme.of(context).textTheme.labelMedium?.copyWith(
                    color: visual.mutedForeground,
                    fontWeight: FontWeight.w900,
                    letterSpacing: 0.8,
                  ),
                ),
              ),
              Icon(
                Icons.groups_2_outlined,
                size: 18,
                color: visual.mutedForeground,
              ),
            ],
          ),
          const SizedBox(height: 14),
          for (var index = 0; index < entries.length; index++) ...[
            _RevealDistributionRow(
              rawLabel: entries[index].key,
              displayLabel: optionLabel(entries[index].key),
              value: entries[index].value,
              color: _distributionColor(visual, index),
              selected: entries[index].key == selectedOption,
            ),
            if (index != entries.length - 1) const SizedBox(height: 14),
          ],
          if (showGapInsight &&
              selectedShare != null &&
              topEntry != null &&
              gapPoints != null) ...[
            const SizedBox(height: 20),
            _GapInsight(
              selectedIsTop: topEntry.key == selectedOption,
              selectedPercent: (selectedShare * 100).round(),
              gapPoints: gapPoints,
            ),
          ],
          const SizedBox(height: 16),
          _MethodologyNote(reveal: reveal),
        ],
      ),
    );
  }
}

class _RevealHeader extends StatelessWidget {
  const _RevealHeader({required this.strings});

  final KefeStrings strings;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 46,
          height: 46,
          decoration: BoxDecoration(
            color: visual.subtleGoldSurface,
            borderRadius: BorderRadius.circular(15),
            border: Border.all(color: visual.gold.withValues(alpha: 0.20)),
          ),
          child: Icon(Icons.insights_rounded, color: visual.goldSoft),
        ),
        const SizedBox(width: 13),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              KefeEyebrow(strings.resultEyebrow),
              const SizedBox(height: 5),
              Text(
                strings.revealTitle,
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w900,
                  height: 1.12,
                  letterSpacing: -0.35,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _PersonalDecision extends StatelessWidget {
  const _PersonalDecision({required this.label, required this.accent});

  final String label;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    return Container(
      key: const ValueKey('reveal-personal-decision'),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            visual.gold.withValues(alpha: visual.isDark ? 0.14 : 0.09),
            accent.withValues(alpha: visual.isDark ? 0.11 : 0.06),
          ],
        ),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: visual.gold.withValues(alpha: 0.30)),
      ),
      child: Row(
        children: [
          Container(
            width: 38,
            height: 38,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: visual.gold.withValues(alpha: 0.12),
            ),
            child: Icon(
              Icons.person_outline_rounded,
              color: visual.goldSoft,
              size: 21,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  strings.yourDecision,
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: visual.goldSoft,
                    fontWeight: FontWeight.w900,
                    letterSpacing: 0.45,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  label,
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w900,
                    height: 1.16,
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

class _RevealDistributionRow extends StatelessWidget {
  const _RevealDistributionRow({
    required this.rawLabel,
    required this.displayLabel,
    required this.value,
    required this.color,
    required this.selected,
  });

  final String rawLabel;
  final String displayLabel;
  final double value;
  final Color color;
  final bool selected;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final duration = KefeMotion.resolve(
      context,
      const Duration(milliseconds: 420),
    );
    final percent = (value * 100).round();

    return Semantics(
      container: true,
      label: displayLabel,
      value: '$percent%',
      selected: selected,
      child: Container(
        key: ValueKey(('reveal-option', rawLabel)),
        padding: const EdgeInsets.fromLTRB(13, 12, 13, 13),
        decoration: BoxDecoration(
          color: selected
              ? color.withValues(alpha: visual.isDark ? 0.09 : 0.055)
              : visual.surfaceSunken,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: selected ? color.withValues(alpha: 0.38) : visual.border,
          ),
        ),
        child: ExcludeSemantics(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: color,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 9),
                  Expanded(
                    child: Text(
                      displayLabel,
                      style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        fontWeight: selected
                            ? FontWeight.w900
                            : FontWeight.w700,
                      ),
                    ),
                  ),
                  if (selected) ...[
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 4,
                      ),
                      decoration: BoxDecoration(
                        color: visual.subtleGoldSurface,
                        borderRadius: BorderRadius.circular(99),
                      ),
                      child: Text(
                        strings.decisionYou,
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: visual.goldSoft,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                    ),
                    const SizedBox(width: 9),
                  ],
                  Text(
                    '$percent%',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      color: color,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              LayoutBuilder(
                builder: (context, constraints) {
                  return Container(
                    height: 9,
                    decoration: BoxDecoration(
                      color: visual.surface,
                      borderRadius: BorderRadius.circular(99),
                      border: Border.all(
                        color: visual.border.withValues(alpha: 0.55),
                      ),
                    ),
                    clipBehavior: Clip.antiAlias,
                    child: Align(
                      alignment: Alignment.centerLeft,
                      child: TweenAnimationBuilder<double>(
                        tween: Tween(
                          begin: 0,
                          end: value.clamp(0.0, 1.0).toDouble(),
                        ),
                        duration: duration,
                        curve: Curves.easeOutCubic,
                        builder: (context, animatedValue, _) => SizedBox(
                          width: constraints.maxWidth * animatedValue,
                          child: DecoratedBox(
                            decoration: BoxDecoration(
                              gradient: LinearGradient(
                                colors: [color.withValues(alpha: 0.74), color],
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  );
                },
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _GapInsight extends StatelessWidget {
  const _GapInsight({
    required this.selectedIsTop,
    required this.selectedPercent,
    required this.gapPoints,
  });

  final bool selectedIsTop;
  final int selectedPercent;
  final int gapPoints;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = selectedIsTop ? visual.success : visual.attention;
    final message = selectedIsTop
        ? strings.gapInsight(selectedIsTop: true, percent: selectedPercent)
        : strings.gapDifferenceInsight(
            selectedPercent: selectedPercent,
            gapPoints: gapPoints,
          );

    return KefeSurface(
      key: const ValueKey('reveal-gap-insight'),
      tone: KefeSurfaceTone.premium,
      padding: const EdgeInsets.all(17),
      borderRadius: 19,
      accent: accent,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: accent.withValues(alpha: 0.13),
              border: Border.all(color: accent.withValues(alpha: 0.25)),
            ),
            child: Icon(
              selectedIsTop
                  ? Icons.balance_rounded
                  : Icons.compare_arrows_rounded,
              color: accent,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                KefeEyebrow(strings.kefeGap, color: visual.goldSoft),
                const SizedBox(height: 6),
                Text(
                  message,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: visual.onSurfaceStrong.withValues(alpha: 0.86),
                    height: 1.46,
                    fontWeight: FontWeight.w600,
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

class _MethodologyNote extends StatelessWidget {
  const _MethodologyNote({required this.reveal});

  final RevealResult reveal;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    return Container(
      key: const ValueKey('reveal-methodology'),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: visual.surfaceSunken,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: visual.border.withValues(alpha: 0.72)),
      ),
      child: Row(
        children: [
          Icon(
            Icons.verified_user_outlined,
            size: 17,
            color: visual.mutedForeground,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              strings.resultMethodologyForLayer(
                layer: reveal.layer,
                sampleSize: reveal.sampleSize,
                confidence: reveal.confidence,
              ),
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: visual.mutedForeground,
                height: 1.35,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

Color _distributionColor(KefeVisualTheme visual, int index) =>
    switch (index % 4) {
      0 => visual.rules,
      1 => visual.empathy,
      2 => visual.gold,
      _ => visual.success,
    };

Color _accentForRawOption(
  KefeVisualTheme visual,
  List<MapEntry<String, double>> entries,
  String rawOption,
) {
  final index = entries.indexWhere((entry) => entry.key == rawOption);
  return _distributionColor(visual, index < 0 ? 2 : index);
}
