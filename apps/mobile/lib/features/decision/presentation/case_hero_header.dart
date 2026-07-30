import 'package:flutter/material.dart';

import '../../../core/design/kefe_theme.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../media_presentation/domain/case_media_models.dart';
import '../../media_presentation/presentation/case_media_surface.dart';
import '../domain/decision_models.dart';

class CaseHeroHeader extends StatelessWidget {
  const CaseHeroHeader({
    required this.caseData,
    required this.flowRuntime,
    super.key,
  });

  final DecisionCase caseData;
  final FlowRuntimeSnapshot flowRuntime;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: KefeColorTokens.gold.withValues(alpha: 0.23)),
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFF10233A), Color(0xFF0D1726), Color(0xFF211A24)],
        ),
      ),
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
                color: KefeColorTokens.rules,
              ),
              _MetaPill(
                icon: Icons.widgets_outlined,
                label: _humanize(caseData.format),
                color: KefeColorTokens.goldSoft,
              ),
              _MetaPill(
                icon: Icons.shield_outlined,
                label: caseData.risk,
                color: _riskColor(caseData.risk),
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
            caseData.title,
            key: const ValueKey('case-title'),
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.w900,
              height: 1.12,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            caseData.summary,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: KefeColorTokens.textMutedDark,
              height: 1.45,
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
                color: KefeColorTokens.goldSoft,
                fontWeight: FontWeight.w900,
                letterSpacing: 0.85,
              ),
            ),
            const Spacer(),
            Text(
              _progressText(steps, strings),
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: KefeColorTokens.textMutedDark,
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
    final visual = _visualFor(step.state);
    return Column(
      children: [
        AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          height: 5,
          decoration: BoxDecoration(
            color: visual.color,
            borderRadius: BorderRadius.circular(99),
          ),
        ),
        const SizedBox(height: 8),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(visual.icon, color: visual.color, size: 13),
            const SizedBox(width: 4),
            Flexible(
              child: Text(
                label,
                textAlign: TextAlign.center,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                  color: visual.color,
                  fontWeight: visual.emphasized
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
  FlowStepRuntimeState state,
) => switch (state) {
  FlowStepRuntimeState.completed => (
    color: KefeColorTokens.success,
    icon: Icons.check_circle_rounded,
    emphasized: false,
  ),
  FlowStepRuntimeState.ready => (
    color: KefeColorTokens.goldSoft,
    icon: Icons.radio_button_checked_rounded,
    emphasized: true,
  ),
  FlowStepRuntimeState.blocked => (
    color: KefeColorTokens.textMutedDark.withValues(alpha: 0.48),
    icon: Icons.lock_outline_rounded,
    emphasized: false,
  ),
  FlowStepRuntimeState.unsupported => (
    color: KefeColorTokens.attention,
    icon: Icons.info_outline_rounded,
    emphasized: false,
  ),
};

Color _riskColor(String risk) => switch (risk.toUpperCase()) {
  'L0' => KefeColorTokens.success,
  'L1' => KefeColorTokens.attention,
  _ => KefeColorTokens.empathy,
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
