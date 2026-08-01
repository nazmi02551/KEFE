import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
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
import 'reveal_result_card.dart';
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
          duration: KefeMotion.resolve(
            context,
            const Duration(milliseconds: 220),
          ),
          child: state.loading
              ? _DecisionLoadingState(
                  key: const ValueKey('loading'),
                  label: strings.loading,
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
    final caseData = state.caseData!;
    final flowRuntime = state.flowRuntime!;
    final productPreviewVisual = ref.watch(productPreviewVisualModeProvider);

    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        if (productPreviewVisual)
          CaseHeroHeader(caseData: caseData, flowRuntime: flowRuntime)
        else
          _ProductionCaseSummaryHeader(caseData: caseData),
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
          _DecisionStatusSurface(
            message: strings.messageForCode(state.errorCode),
            offlineDraft: state.offlineDraft,
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
            ? _CapabilityPendingSurface(step: step)
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
      return _CapabilityPendingSurface(step: step);
    }
    if (step.state != FlowStepRuntimeState.ready) {
      return const SizedBox.shrink();
    }

    final strings = KefeStrings.of(context);
    final caseData = state.caseData!;
    final reasonPolicy = caseData.reasonPolicy;
    final controller = ref.read(decisionControllerProvider.notifier);
    final inputsEnabled = !state.recoveryPending && !state.submitting;
    final action = !state.hasRequiredResponses || state.submitting
        ? null
        : state.recoveryPending
        ? controller.retryPending
        : controller.commit;

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
        _CommitActionPanel(
          onPressed: action,
          submitting: state.submitting,
          recoveryPending: state.recoveryPending,
          hasRequiredResponses: state.hasRequiredResponses,
        ),
        const SizedBox(height: 20),
      ],
    );
  }

  Widget _reflectionStep() {
    if (step.state == FlowStepRuntimeState.unsupported) {
      return _CapabilityPendingSurface(step: step);
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
      return _CapabilityPendingSurface(step: step);
    }
    if (step.state != FlowStepRuntimeState.ready || state.reveal == null) {
      return const SizedBox.shrink();
    }

    final controller = ref.read(decisionControllerProvider.notifier);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        RevealResultCard(
          reveal: state.reveal!,
          selectedOption: state.selectedOption,
        ),
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

class _ProductionCaseSummaryHeader extends StatelessWidget {
  const _ProductionCaseSummaryHeader({required this.caseData});

  final DecisionCase caseData;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return KefeSurface(
      key: const ValueKey('production-case-summary-header'),
      tone: KefeSurfaceTone.premium,
      padding: const EdgeInsets.all(20),
      borderRadius: 26,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ExcludeSemantics(
                child: Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: visual.subtleGoldSurface,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(
                      color: visual.gold.withValues(alpha: 0.28),
                    ),
                  ),
                  child: Icon(
                    Icons.balance_rounded,
                    color: visual.goldSoft,
                    size: 24,
                  ),
                ),
              ),
              const SizedBox(width: 13),
              Expanded(
                child: Text(
                  caseData.title,
                  key: const ValueKey('case-title'),
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    color: visual.onSurfaceStrong,
                    fontWeight: FontWeight.w900,
                    height: 1.14,
                    letterSpacing: -0.35,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Text(
            caseData.summary,
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: visual.onSurfaceStrong.withValues(alpha: 0.74),
              height: 1.46,
            ),
          ),
        ],
      ),
    );
  }
}

class _DecisionLoadingState extends StatelessWidget {
  const _DecisionLoadingState({required this.label, super.key});

  final String label;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Semantics(
          liveRegion: true,
          label: label,
          child: KefeSurface(
            tone: KefeSurfaceTone.raised,
            accent: visual.gold,
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                ExcludeSemantics(
                  child: Icon(
                    Icons.hourglass_top_rounded,
                    color: visual.goldSoft,
                  ),
                ),
                const SizedBox(width: 12),
                Flexible(
                  child: Text(
                    label,
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _CommitActionPanel extends StatelessWidget {
  const _CommitActionPanel({
    required this.onPressed,
    required this.submitting,
    required this.recoveryPending,
    required this.hasRequiredResponses,
  });

  final VoidCallback? onPressed;
  final bool submitting;
  final bool recoveryPending;
  final bool hasRequiredResponses;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final helper = !hasRequiredResponses
        ? strings.completeRequired
        : recoveryPending
        ? strings.pendingHelper
        : strings.commitHelper;
    final buttonLabel = submitting
        ? strings.loading
        : recoveryPending
        ? strings.retrySync
        : strings.commit;

    return KefeSurface(
      key: const ValueKey('commit-action-panel'),
      tone: KefeSurfaceTone.raised,
      accent: recoveryPending ? visual.attention : visual.gold,
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Semantics(
            liveRegion: submitting,
            child: FilledButton.icon(
              key: const ValueKey('commit-button'),
              onPressed: onPressed,
              icon: Icon(
                submitting
                    ? Icons.hourglass_top_rounded
                    : recoveryPending
                    ? Icons.sync_rounded
                    : Icons.lock_rounded,
              ),
              label: Text(buttonLabel),
            ),
          ),
          const SizedBox(height: 10),
          Text(
            helper,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: visual.mutedForeground,
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }
}

class _DecisionStatusSurface extends StatelessWidget {
  const _DecisionStatusSurface({
    required this.message,
    required this.offlineDraft,
  });

  final String message;
  final bool offlineDraft;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final accent = offlineDraft
        ? visual.attention
        : Theme.of(context).colorScheme.error;
    return Semantics(
      liveRegion: true,
      child: KefeSurface(
        tone: KefeSurfaceTone.sunken,
        accent: accent,
        padding: const EdgeInsets.all(15),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ExcludeSemantics(
              child: Icon(
                offlineDraft
                    ? Icons.cloud_off_rounded
                    : Icons.error_outline_rounded,
                color: accent,
                size: 21,
              ),
            ),
            const SizedBox(width: 11),
            Expanded(
              child: Text(
                message,
                key: const ValueKey('decision-status-message'),
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: visual.foreground,
                  height: 1.42,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CapabilityPendingSurface extends StatelessWidget {
  const _CapabilityPendingSurface({required this.step});

  final FlowRuntimeStep step;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    return KefeSurface(
      key: ValueKey('capability-pending-${step.code}'),
      tone: KefeSurfaceTone.raised,
      accent: visual.attention,
      padding: const EdgeInsets.all(18),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ExcludeSemantics(
            child: Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: visual.attention.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(13),
                border: Border.all(
                  color: visual.attention.withValues(alpha: 0.26),
                ),
              ),
              child: Icon(
                Icons.info_outline_rounded,
                color: visual.attention,
                size: 21,
              ),
            ),
          ),
          const SizedBox(width: 13),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  strings.flowCapabilityPendingTitle,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  strings.flowCapabilityPendingBody(step.reasonCode),
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: visual.mutedForeground,
                    height: 1.42,
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

class _FirstUseCompletionCard extends StatelessWidget {
  const _FirstUseCompletionCard({required this.onContinue});

  final VoidCallback onContinue;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    return KefeSurface(
      key: const ValueKey('first-use-completion'),
      tone: KefeSurfaceTone.premium,
      accent: visual.success,
      padding: const EdgeInsets.all(20),
      borderRadius: 24,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: visual.success.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(
                    color: visual.success.withValues(alpha: 0.34),
                  ),
                ),
                child: ExcludeSemantics(
                  child: Icon(
                    Icons.check_rounded,
                    color: visual.success,
                    size: 26,
                  ),
                ),
              ),
              const SizedBox(width: 13),
              Expanded(
                child: Text(
                  strings.firstRevealHelper,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: visual.onSurfaceStrong,
                    fontWeight: FontWeight.w800,
                    height: 1.35,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 18),
          FilledButton.icon(
            key: const ValueKey('continue-as-guest'),
            onPressed: onContinue,
            icon: const Icon(Icons.arrow_forward_rounded),
            label: Text(strings.continueAsGuest),
          ),
        ],
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
    final visual = context.kefeVisual;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Semantics(
          liveRegion: true,
          child: KefeSurface(
            tone: KefeSurfaceTone.raised,
            accent: Theme.of(context).colorScheme.error,
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                ExcludeSemantics(
                  child: Icon(
                    Icons.error_outline_rounded,
                    color: Theme.of(context).colorScheme.error,
                    size: 30,
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  message,
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    color: visual.foreground,
                    height: 1.42,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 16),
                FilledButton(onPressed: onRetry, child: Text(retryLabel)),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
