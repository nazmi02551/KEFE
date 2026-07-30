import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_content_localizer.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../media_presentation/domain/case_media_models.dart';
import '../../media_presentation/presentation/case_media_surface.dart';
import '../domain/decision_models.dart';

class CaseHeroHeader extends ConsumerWidget {
  const CaseHeroHeader({
    required this.caseData,
    required this.flowRuntime,
    super.key,
  });

  final DecisionCase caseData;
  final FlowRuntimeSnapshot flowRuntime;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = KefeStrings.of(context);
    final content = ref.watch(kefeContentLocalizerProvider);
    final visual = context.kefeVisual;
    final title = content.text(
      namespace: KefeContentNamespace.caseTitle,
      id: caseData.id,
      locale: strings.locale,
      fallback: caseData.title,
    );
    final summary = content.text(
      namespace: KefeContentNamespace.caseSummary,
      id: caseData.id,
      locale: strings.locale,
      fallback: caseData.summary,
    );

    return KefeSurface(
      tone: KefeSurfaceTone.premium,
      padding: const EdgeInsets.all(19),
      borderRadius: 26,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _MetaPill(
                icon: _domainIcon(caseData.domain),
                label: strings.domainName(caseData.domain),
                color: visual.rules,
              ),
              _MetaPill(
                icon: Icons.widgets_outlined,
                label: _humanize(caseData.format),
                color: visual.goldSoft,
              ),
              _MetaPill(
                icon: Icons.shield_outlined,
                label: caseData.risk,
                color: _riskColor(visual, caseData.risk),
              ),
            ],
          ),
          const SizedBox(height: 16),
          CaseMediaSurface(
            caseVersionId: caseData.versionId,
            slot: CaseMediaSlot.caseHero,
            borderRadius: 18,
          ),
          const SizedBox(height: 18),
          Text(
            title,
            key: const ValueKey('case-title'),
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              color: visual.onSurfaceStrong,
              fontWeight: FontWeight.w900,
              height: 1.12,
              letterSpacing: -0.35,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            summary,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: visual.onSurfaceStrong.withValues(alpha: 0.72),
              height: 1.48,
            ),
          ),
          const SizedBox(height: 20),
          _FlowProgressRail(flowRuntime: flowRuntime),
        ],
      ),
    );
  }
}

class _FlowProgressRail extends StatelessWidget {
  const _FlowProgressRail({required this.flowRuntime});

  final FlowRuntimeSnapshot flowRuntime;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final steps = flowRuntime.steps;
    if (steps.isEmpty) return const SizedBox.shrink();

    final counts = <String, int>{};
    final totals = <String, int>{};
    for (final step in steps) {
      totals.update(
        step.primitiveCode,
        (value) => value + 1,
        ifAbsent: () => 1,
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Text(
              strings.journeyLabel,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: visual.goldSoft,
                fontWeight: FontWeight.w900,
                letterSpacing: 0.85,
              ),
            ),
            const Spacer(),
            Text(
              _progressText(steps, strings),
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: visual.onSurfaceStrong.withValues(alpha: 0.62),
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        LayoutBuilder(
          builder: (context, constraints) {
            final itemWidth =
                (constraints.maxWidth - (steps.length - 1) * 6) / steps.length;
            return Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                for (var index = 0; index < steps.length; index++) ...[
                  SizedBox(
                    width: itemWidth,
                    child: _ProgressStep(
                      step: steps[index],
                      label: _labelFor(
                        steps[index],
                        counts: counts,
                        totals: totals,
                        strings: strings,
                      ),
                    ),
                  ),
                  if (index != steps.length - 1) const SizedBox(width: 6),
                ],
              ],
            );
          },
        ),
      ],
    );
  }

  String _labelFor(
    FlowRuntimeStep step, {
    required Map<String, int> counts,
    required Map<String, int> totals,
    required KefeStrings strings,
  }) {
    final order = counts.update(
      step.primitiveCode,
      (value) => value + 1,
      ifAbsent: () => 1,
    );
    final base = switch (step.primitiveCode) {
      'CONTEXT' => strings.stepCase,
      'DECISION' => strings.stepWeigh,
      'COLLECTIVE_RESULT' => strings.stepResult,
      'REFLECTION' => strings.stepReflection,
      _ => _humanize(step.primitiveCode),
    };
    return (totals[step.primitiveCode] ?? 0) > 1 ? '$base $order' : base;
  }

  String _progressText(List<FlowRuntimeStep> steps, KefeStrings strings) {
    final completed = steps
        .where((step) => step.state == FlowStepRuntimeState.completed)
        .length;
    final ready = steps
        .where((step) => step.state == FlowStepRuntimeState.ready)
        .length;
    if (completed == steps.length) return strings.stepCompleted;
    if (ready > 0) return '${completed + 1}/${steps.length}';
    return '$completed/${steps.length}';
  }
}

class _ProgressStep extends StatelessWidget {
  const _ProgressStep({required this.step, required this.label});

  final FlowRuntimeStep step;
  final String label;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final stateVisual = _visualFor(visual, step.state);
    return Column(
      children: [
        AnimatedContainer(
          duration: KefeMotion.resolve(
            context,
            const Duration(milliseconds: 180),
          ),
          height: 5,
          decoration: BoxDecoration(
            color: stateVisual.color,
            borderRadius: BorderRadius.circular(99),
          ),
        ),
        const SizedBox(height: 8),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(stateVisual.icon, color: stateVisual.color, size: 13),
            const SizedBox(width: 4),
            Flexible(
              child: Text(
                label,
                textAlign: TextAlign.center,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                  color: stateVisual.color,
                  fontWeight: stateVisual.emphasized
                      ? FontWeight.w900
                      : FontWeight.w600,
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _MetaPill extends StatelessWidget {
  const _MetaPill({
    required this.icon,
    required this.label,
    required this.color,
  });

  final IconData icon;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.09),
        borderRadius: BorderRadius.circular(99),
        border: Border.all(color: color.withValues(alpha: 0.22)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 5),
          Text(
            label,
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: color,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }
}

({Color color, IconData icon, bool emphasized}) _visualFor(
  KefeVisualTheme visual,
  FlowStepRuntimeState state,
) => switch (state) {
  FlowStepRuntimeState.completed => (
    color: visual.success,
    icon: Icons.check_circle_rounded,
    emphasized: false,
  ),
  FlowStepRuntimeState.ready => (
    color: visual.goldSoft,
    icon: Icons.radio_button_checked_rounded,
    emphasized: true,
  ),
  FlowStepRuntimeState.blocked => (
    color: visual.onSurfaceStrong.withValues(alpha: 0.36),
    icon: Icons.lock_outline_rounded,
    emphasized: false,
  ),
  FlowStepRuntimeState.unsupported => (
    color: visual.attention,
    icon: Icons.info_outline_rounded,
    emphasized: false,
  ),
};

Color _riskColor(KefeVisualTheme visual, String risk) =>
    switch (risk.toUpperCase()) {
      'L0' => visual.success,
      'L1' => visual.attention,
      _ => visual.empathy,
    };

IconData _domainIcon(String domain) => switch (domain) {
  'SPORTS' => Icons.sports_soccer_rounded,
  'CIVIC' => Icons.account_balance_outlined,
  'TECHNOLOGY' => Icons.memory_rounded,
  'WORK_ECONOMY' => Icons.work_outline_rounded,
  'EDUCATION' => Icons.school_outlined,
  'DAILY_LIFE' => Icons.people_alt_outlined,
  _ => Icons.public_rounded,
};

String _humanize(String value) {
  final words = value
      .split('_')
      .where((word) => word.isNotEmpty)
      .map(
        (word) => word.length == 1
            ? word.toUpperCase()
            : '${word[0].toUpperCase()}${word.substring(1).toLowerCase()}',
      );
  return words.join(' ');
}
