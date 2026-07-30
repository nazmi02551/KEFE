import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/design/kefe_theme.dart';
import '../../../core/design/product_preview_visual_mode.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../context/presentation/context_section.dart';
import '../../onboarding/application/onboarding_controller.dart';
import '../application/decision_controller.dart';
import '../domain/decision_models.dart';
import 'case_hero_header.dart';
import 'perspective_section.dart';
import 'question_input.dart';
import 'reason_input.dart';
import 'reflection_step.dart';

class DecisionFlowScreen extends ConsumerStatefulWidget {
  const DecisionFlowScreen({
    required this.caseId,
    this.firstUse = false,
    super.key,
  });

  final String caseId;
  final bool firstUse;

  @override
  ConsumerState<DecisionFlowScreen> createState() => _DecisionFlowScreenState();
}

class _DecisionFlowScreenState extends ConsumerState<DecisionFlowScreen> {
  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void didUpdateWidget(covariant DecisionFlowScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.caseId != widget.caseId) {
      _load();
    }
  }

  void _load() {
    Future.microtask(
      () => ref.read(decisionControllerProvider.notifier).load(widget.caseId),
    );
  }

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final state = ref.watch(decisionControllerProvider);

    ref.listen<DecisionState>(decisionControllerProvider, (
      previous,
      next,
    ) async {
      if (widget.firstUse && previous?.reveal == null && next.reveal != null) {
        await ref.read(onboardingControllerProvider).complete();
      }
    });

    return Scaffold(
      appBar: AppBar(title: Text(strings.appName)),
      body: SafeArea(
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 220),
          child: state.loading
              ? Center(
                  key: const ValueKey('loading'),
                  child: Semantics(
                    label: strings.loading,
                    child: const CircularProgressIndicator(),
                  ),
                )
              : state.caseData == null || state.flowRuntime == null
              ? _ErrorState(
                  key: const ValueKey('error'),
                  message: strings.messageForCode(state.errorCode),
                  retryLabel: strings.retry,
                  onRetry: _load,
                )
              : _DecisionContent(
                  key: ValueKey('content-${state.caseData!.id}'),
                  state: state,
                  firstUse: widget.firstUse,
                ),
        ),
      ),
    );
  }
}

class _DecisionContent extends ConsumerWidget {
  const _DecisionContent({
    required this.state,
    required this.firstUse,
    super.key,
  });

  final DecisionState state;
  final bool firstUse;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = KefeStrings.of(context);
    final caseData = state.caseData!;
    final flowRuntime = state.flowRuntime!;
    final productPreviewVisual = ref.watch(productPreviewVisualModeProvider);

    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        if (productPreviewVisual)
          CaseHeroHeader(caseData: caseData, flowRuntime: flowRuntime)
        else ...[
          Text(
            caseData.title,
            key: const ValueKey('case-title'),
            style: Theme.of(context).textTheme.headlineMedium,
          ),
          const SizedBox(height: 12),
          Text(caseData.summary, style: Theme.of(context).textTheme.bodyLarge),
        ],
        const SizedBox(height: 20),
        for (final step in flowRuntime.steps)
          _FlowStepSection(
            key: ValueKey('flow-step-${step.code}'),
            step: step,
            state: state,
            firstUse: firstUse,
          ),
        if (state.errorCode != null) ...[
          const SizedBox(height: 16),
          Semantics(
            liveRegion: true,
            child: Text(
              strings.messageForCode(state.errorCode),
              key: const ValueKey('decision-status-message'),
              style: TextStyle(
                color: state.offlineDraft
                    ? Theme.of(context).colorScheme.secondary
                    : Theme.of(context).colorScheme.error,
              ),
              textAlign: TextAlign.center,
            ),
          ),
        ],
      ],
    );
  }
}

class _FlowStepSection extends ConsumerWidget {
  const _FlowStepSection({
    required this.step,
    required this.state,
    required this.firstUse,
    super.key,
  });

  final FlowRuntimeStep step;
  final DecisionState state;
  final bool firstUse;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (step.state == FlowStepRuntimeState.blocked) {
      return const SizedBox.shrink();
    }

    return switch (step.primitiveCode) {
      'CONTEXT' => _contextStep(ref),
      'DECISION' => _decisionStep(context, ref),
      'COLLECTIVE_RESULT' => _resultStep(context, ref),
      'REFLECTION' => _reflectionStep(),
      _ =>
        step.state == FlowStepRuntimeState.unsupported
            ? _CapabilityPendingCard(step: step)
            : const SizedBox.shrink(),
    };
  }

  Widget _contextStep(WidgetRef ref) {
    if (step.state != FlowStepRuntimeState.ready &&
        step.state != FlowStepRuntimeState.completed) {
      return const SizedBox.shrink();
    }
    return _ExposureAwareContextStep(
      caseVersionId: state.caseData!.versionId,
      stepCode: step.code,
      shouldRecordExposure:
          step.state == FlowStepRuntimeState.ready && !state.offlineDraft,
      onExposed: () => ref
          .read(decisionControllerProvider.notifier)
          .recordContextExposure(step.code),
    );
  }

  Widget _decisionStep(BuildContext context, WidgetRef ref) {
    if (step.state == FlowStepRuntimeState.unsupported) {
      return _CapabilityPendingCard(step: step);
    }
    if (step.state != FlowStepRuntimeState.ready) {
      return const SizedBox.shrink();
    }

    final strings = KefeStrings.of(context);
    final caseData = state.caseData!;
    final reasonPolicy = caseData.reasonPolicy;
    final controller = ref.read(decisionControllerProvider.notifier);
    final inputsEnabled = !state.recoveryPending && !state.submitting;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final question in caseData.questions) ...[
          QuestionInputCard(
            question: question,
            value: state.responseFor(question.id),
            enabled: inputsEnabled,
            onChanged: (value) => controller.setResponse(question.id, value),
          ),
          const SizedBox(height: 12),
        ],
        if (reasonPolicy != null) ...[
          ReasonInputCard(
            policy: reasonPolicy,
            selectedTags: state.reasonTags,
            text: state.reasonText,
            enabled: inputsEnabled,
            onTagToggled: controller.toggleReasonTag,
            onTextChanged: controller.setReasonText,
          ),
          const SizedBox(height: 12),
        ],
        const SizedBox(height: 8),
        FilledButton(
          key: const ValueKey('commit-button'),
          onPressed: !state.hasRequiredResponses || state.submitting
              ? null
              : state.recoveryPending
              ? controller.retryPending
              : controller.commit,
          child: state.submitting
              ? const SizedBox.square(
                  dimension: 22,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : Text(
                  state.recoveryPending ? strings.retrySync : strings.commit,
                ),
        ),
        const SizedBox(height: 8),
        Text(
          !state.hasRequiredResponses
              ? strings.completeRequired
              : state.recoveryPending
              ? strings.pendingHelper
              : strings.commitHelper,
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 20),
      ],
    );
  }

  Widget _reflectionStep() {
    if (step.state == FlowStepRuntimeState.unsupported) {
      return _CapabilityPendingCard(step: step);
    }
    if (step.state != FlowStepRuntimeState.ready &&
        step.state != FlowStepRuntimeState.completed) {
      return const SizedBox.shrink();
    }
    return ReflectionStepCard(
      sessionId: state.sessionId!,
      caseVersionId: state.caseData!.versionId,
      step: step,
    );
  }

  Widget _resultStep(BuildContext context, WidgetRef ref) {
    if (step.state == FlowStepRuntimeState.unsupported) {
      return _CapabilityPendingCard(step: step);
    }
    if (step.state != FlowStepRuntimeState.ready || state.reveal == null) {
      return const SizedBox.shrink();
    }

    final controller = ref.read(decisionControllerProvider.notifier);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _RevealCard(state: state),
        const SizedBox(height: 20),
        PerspectiveSection(
          state: state.perspectiveState,
          result: state.perspective,
          reasonPendingModeration: state.reasonPendingModeration,
          onRetry: controller.retryPerspective,
        ),
        if (firstUse) ...[
          const SizedBox(height: 20),
          _FirstUseCompletionCard(onContinue: () => context.go('/explore')),
        ],
      ],
    );
  }
}

class _ExposureAwareContextStep extends StatefulWidget {
  const _ExposureAwareContextStep({
    required this.caseVersionId,
    required this.stepCode,
    required this.shouldRecordExposure,
    required this.onExposed,
  });

  final String caseVersionId;
  final String stepCode;
  final bool shouldRecordExposure;
  final VoidCallback onExposed;

  @override
  State<_ExposureAwareContextStep> createState() =>
      _ExposureAwareContextStepState();
}

class _ExposureAwareContextStepState extends State<_ExposureAwareContextStep> {
  bool _scheduled = false;

  @override
  void initState() {
    super.initState();
    _scheduleExposure();
  }

  @override
  void didUpdateWidget(covariant _ExposureAwareContextStep oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.stepCode != widget.stepCode) {
      _scheduled = false;
    }
    _scheduleExposure();
  }

  void _scheduleExposure() {
    if (!widget.shouldRecordExposure || _scheduled) return;
    _scheduled = true;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      widget.onExposed();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        ContextSection(caseVersionId: widget.caseVersionId),
        const SizedBox(height: 24),
      ],
    );
  }
}

class _CapabilityPendingCard extends StatelessWidget {
  const _CapabilityPendingCard({required this.step});

  final FlowRuntimeStep step;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    return Card(
      key: ValueKey('capability-pending-${step.code}'),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              strings.flowCapabilityPendingTitle,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Text(strings.flowCapabilityPendingBody(step.reasonCode)),
          ],
        ),
      ),
    );
  }
}

class _RevealCard extends StatelessWidget {
  const _RevealCard({required this.state});

  final DecisionState state;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final reveal = state.reveal!;
    final entries = reveal.values.entries.toList(growable: false);
    final selectedOption = state.selectedOption;
    final selectedShare = selectedOption == null
        ? null
        : reveal.values[selectedOption];
    final topEntry = entries.isEmpty
        ? null
        : entries.reduce((a, b) => a.value >= b.value ? a : b);
    final gapPoints = selectedShare == null || topEntry == null
        ? null
        : ((topEntry.value - selectedShare).abs() * 100).round();

    return Card(
      key: const ValueKey('reveal-card'),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Container(
                  width: 42,
                  height: 42,
                  decoration: BoxDecoration(
                    color: KefeColorTokens.gold.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(13),
                  ),
                  child: const Icon(
                    Icons.insights_rounded,
                    color: KefeColorTokens.goldSoft,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'SONUÇLAR',
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: KefeColorTokens.goldSoft,
                          fontWeight: FontWeight.w900,
                          letterSpacing: 0.9,
                        ),
                      ),
                      const SizedBox(height: 3),
                      Text(
                        strings.revealTitle,
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            if (selectedOption != null) ...[
              const SizedBox(height: 16),
              Container(
                key: const ValueKey('reveal-personal-decision'),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: KefeColorTokens.gold.withValues(alpha: 0.07),
                  borderRadius: BorderRadius.circular(15),
                  border: Border.all(
                    color: KefeColorTokens.gold.withValues(alpha: 0.24),
                  ),
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.person_outline_rounded,
                      color: KefeColorTokens.goldSoft,
                      size: 21,
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'SENİN KARARIN',
                            style: Theme.of(context).textTheme.labelSmall
                                ?.copyWith(
                                  color: KefeColorTokens.goldSoft,
                                  fontWeight: FontWeight.w900,
                                ),
                          ),
                          const SizedBox(height: 3),
                          Text(
                            selectedOption,
                            style: Theme.of(context).textTheme.titleMedium
                                ?.copyWith(fontWeight: FontWeight.w800),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
            const SizedBox(height: 18),
            Text(
              'TOPLULUK DAĞILIMI',
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: KefeColorTokens.textMutedDark,
                fontWeight: FontWeight.w900,
                letterSpacing: 0.8,
              ),
            ),
            const SizedBox(height: 12),
            for (var index = 0; index < entries.length; index++) ...[
              _RevealDistributionRow(
                label: entries[index].key,
                value: entries[index].value,
                color: _distributionColor(index),
                selected: entries[index].key == selectedOption,
              ),
              if (index != entries.length - 1) const SizedBox(height: 13),
            ],
            if (selectedShare != null &&
                topEntry != null &&
                gapPoints != null) ...[
              const SizedBox(height: 18),
              Container(
                key: const ValueKey('reveal-gap-insight'),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: KefeColorTokens.surfaceElevatedDark.withValues(
                    alpha: 0.72,
                  ),
                  borderRadius: BorderRadius.circular(15),
                  border: Border.all(
                    color: Theme.of(context).colorScheme.outlineVariant,
                  ),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(
                      topEntry.key == selectedOption
                          ? Icons.balance_rounded
                          : Icons.compare_arrows_rounded,
                      color: topEntry.key == selectedOption
                          ? KefeColorTokens.success
                          : KefeColorTokens.attention,
                    ),
                    const SizedBox(width: 11),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'KEFE UÇURUMU',
                            style: Theme.of(context).textTheme.labelSmall
                                ?.copyWith(
                                  color: KefeColorTokens.goldSoft,
                                  fontWeight: FontWeight.w900,
                                  letterSpacing: 0.7,
                                ),
                          ),
                          const SizedBox(height: 5),
                          Text(
                            topEntry.key == selectedOption
                                ? 'Seçimin toplulukta en yüksek paya sahip. Katılımcıların %${(selectedShare * 100).round()} kadarı aynı seçeneği tercih etti.'
                                : 'Seçtiğin seçenek toplulukta %${(selectedShare * 100).round()}. En yüksek paya sahip seçenekle fark $gapPoints yüzde puan.',
                            style: Theme.of(
                              context,
                            ).textTheme.bodyMedium?.copyWith(height: 1.4),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
            const SizedBox(height: 14),
            Text(
              '${strings.trustedSample} · '
              'n=${reveal.sampleSize} · ${reveal.confidence}',
              key: const ValueKey('reveal-methodology'),
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: KefeColorTokens.textMutedDark,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _distributionColor(int index) => switch (index % 4) {
    0 => KefeColorTokens.rules,
    1 => KefeColorTokens.empathy,
    2 => KefeColorTokens.gold,
    _ => KefeColorTokens.success,
  };
}

class _RevealDistributionRow extends StatelessWidget {
  const _RevealDistributionRow({
    required this.label,
    required this.value,
    required this.color,
    required this.selected,
  });

  final String label;
  final double value;
  final Color color;
  final bool selected;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                label,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontWeight: selected ? FontWeight.w900 : FontWeight.w700,
                ),
              ),
            ),
            if (selected) ...[
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                decoration: BoxDecoration(
                  color: KefeColorTokens.gold.withValues(alpha: 0.11),
                  borderRadius: BorderRadius.circular(99),
                ),
                child: Text(
                  'Sen',
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: KefeColorTokens.goldSoft,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
              const SizedBox(width: 8),
            ],
            Text(
              '%${(value * 100).round()}',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                color: color,
                fontWeight: FontWeight.w900,
              ),
            ),
          ],
        ),
        const SizedBox(height: 7),
        ClipRRect(
          borderRadius: BorderRadius.circular(99),
          child: LinearProgressIndicator(
            minHeight: 8,
            value: value,
            backgroundColor: KefeColorTokens.surfaceSoftDark,
            valueColor: AlwaysStoppedAnimation(color),
          ),
        ),
      ],
    );
  }
}

class _FirstUseCompletionCard extends StatelessWidget {
  const _FirstUseCompletionCard({required this.onContinue});

  final VoidCallback onContinue;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    return Card(
      key: const ValueKey('first-use-completion'),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(strings.firstRevealHelper),
            const SizedBox(height: 16),
            FilledButton(
              key: const ValueKey('continue-as-guest'),
              onPressed: onContinue,
              child: Text(strings.continueAsGuest),
            ),
          ],
        ),
      ),
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({
    required this.message,
    required this.retryLabel,
    required this.onRetry,
    super.key,
  });

  final String message;
  final String retryLabel;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton(onPressed: onRetry, child: Text(retryLabel)),
          ],
        ),
      ),
    );
  }
}
