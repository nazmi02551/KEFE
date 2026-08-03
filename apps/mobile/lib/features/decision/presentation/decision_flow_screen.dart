import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/config/experience_presentation_config.dart';
import '../../../core/design/kefe_active_journey.dart';
import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/design/product_preview_visual_mode.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../context/presentation/context_section.dart';
import '../../onboarding/application/onboarding_controller.dart';
import '../../progress/presentation/progress_section.dart';
import '../application/decision_controller.dart';
import '../domain/decision_models.dart';
import 'case_hero_header.dart';
import 'decision_journey_stage_resolver.dart';
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
    final experience = ref.watch(experiencePresentationConfigProvider);

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
              : experience.decisionJourneyMode ==
                    DecisionJourneyPresentationMode.progressive
              ? _ProgressiveDecisionContent(
                  key: ValueKey('progressive-content-${state.caseData!.id}'),
                  state: state,
                  firstUse: widget.firstUse,
                )
              : _LegacyDecisionContent(
                  key: ValueKey('legacy-content-${state.caseData!.id}'),
                  state: state,
                  firstUse: widget.firstUse,
                ),
        ),
      ),
    );
  }
}

class _ProgressiveDecisionContent extends ConsumerStatefulWidget {
  const _ProgressiveDecisionContent({
    required this.state,
    required this.firstUse,
    super.key,
  });

  final DecisionState state;
  final bool firstUse;

  @override
  ConsumerState<_ProgressiveDecisionContent> createState() =>
      _ProgressiveDecisionContentState();
}

class _ProgressiveDecisionContentState
    extends ConsumerState<_ProgressiveDecisionContent> {
  bool _showPerspectives = false;

  @override
  void didUpdateWidget(covariant _ProgressiveDecisionContent oldWidget) {
    super.didUpdateWidget(oldWidget);
    final previousStep = DecisionJourneyStageResolver.primary(
      oldWidget.state.flowRuntime!,
    );
    final nextStep = DecisionJourneyStageResolver.primary(
      widget.state.flowRuntime!,
    );
    if (oldWidget.state.caseData?.id != widget.state.caseData?.id ||
        previousStep?.code != nextStep?.code ||
        widget.state.reveal == null) {
      _showPerspectives = false;
    }
  }

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final state = widget.state;
    final caseData = state.caseData!;
    final flowRuntime = state.flowRuntime!;
    final productPreviewVisual = ref.watch(productPreviewVisualModeProvider);
    final activeStep = DecisionJourneyStageResolver.primary(flowRuntime);

    return ListView(
      key: const ValueKey('progressive-decision-journey'),
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
        if (activeStep == null)
          _JourneyUnavailableCard(message: strings.flowRuntimeUnavailable)
        else
          KefeActiveJourney(
            stageId: activeStep.code,
            eyebrow: strings.activeJourneyEyebrow,
            title: strings.activeJourneyTitle(activeStep.primitiveCode),
            subtitle: strings.activeJourneyHelper,
            progressLabel: strings.activeJourneyProgress(
              DecisionJourneyStageResolver.ordinal(flowRuntime, activeStep),
              flowRuntime.steps.length,
            ),
            icon: _iconForPrimitive(activeStep.primitiveCode),
            child: _FlowStepSection(
              key: ValueKey('active-flow-step-${activeStep.code}'),
              step: activeStep,
              state: state,
              firstUse: widget.firstUse,
              progressiveContextAdvance: true,
              progressiveResultDisclosure: true,
              showPerspectives: _showPerspectives,
              onShowPerspectives: () {
                setState(() => _showPerspectives = true);
              },
            ),
          ),
        if (state.errorCode != null) ...[
          const SizedBox(height: 16),
          _DecisionStatusMessage(state: state),
        ],
      ],
    );
  }
}

class _LegacyDecisionContent extends ConsumerWidget {
  const _LegacyDecisionContent({
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
      key: const ValueKey('legacy-decision-long-scroll'),
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
          _DecisionStatusMessage(state: state),
        ],
      ],
    );
  }
}

class _DecisionStatusMessage extends StatelessWidget {
  const _DecisionStatusMessage({required this.state});

  final DecisionState state;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    return Semantics(
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
    );
  }
}

class _FlowStepSection extends ConsumerWidget {
  const _FlowStepSection({
    required this.step,
    required this.state,
    required this.firstUse,
    this.progressiveContextAdvance = false,
    this.progressiveResultDisclosure = false,
    this.showPerspectives = true,
    this.onShowPerspectives,
    super.key,
  });

  final FlowRuntimeStep step;
  final DecisionState state;
  final bool firstUse;
  final bool progressiveContextAdvance;
  final bool progressiveResultDisclosure;
  final bool showPerspectives;
  final VoidCallback? onShowPerspectives;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (step.state == FlowStepRuntimeState.blocked) {
      return const SizedBox.shrink();
    }

    return switch (step.primitiveCode) {
      'CONTEXT' => _contextStep(context, ref),
      'DECISION' => _decisionStep(context, ref),
      'COLLECTIVE_RESULT' => _resultStep(context, ref),
      'REFLECTION' => _reflectionStep(),
      _ =>
        step.state == FlowStepRuntimeState.unsupported
            ? _CapabilityPendingCard(step: step)
            : const SizedBox.shrink(),
    };
  }

  Widget _contextStep(BuildContext context, WidgetRef ref) {
    if (step.state != FlowStepRuntimeState.ready &&
        step.state != FlowStepRuntimeState.completed) {
      return const SizedBox.shrink();
    }

    void onExposed() {
      ref
          .read(decisionControllerProvider.notifier)
          .recordContextExposure(step.code);
    }

    if (progressiveContextAdvance &&
        step.state == FlowStepRuntimeState.ready) {
      return _ProgressiveContextStep(
        caseVersionId: state.caseData!.versionId,
        enabled: !state.offlineDraft,
        onContinue: onExposed,
      );
    }

    return _ExposureAwareContextStep(
      caseVersionId: state.caseData!.versionId,
      stepCode: step.code,
      shouldRecordExposure:
          step.state == FlowStepRuntimeState.ready && !state.offlineDraft,
      onExposed: onExposed,
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

    final strings = KefeStrings.of(context);
    final controller = ref.read(decisionControllerProvider.notifier);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        RevealResultCard(
          reveal: state.reveal!,
          selectedOption: state.selectedOption,
        ),
        if (progressiveResultDisclosure && !showPerspectives) ...[
          const SizedBox(height: 16),
          KefeSurface(
            key: const ValueKey('perspective-disclosure-prompt'),
            tone: KefeSurfaceTone.raised,
            borderRadius: 18,
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  strings.perspectiveDisclosureTitle,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: context.kefeVisual.foreground,
                        fontWeight: FontWeight.w900,
                      ),
                ),
                const SizedBox(height: 7),
                Text(
                  strings.perspectiveDisclosureBody,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: context.kefeVisual.mutedForeground,
                        height: 1.4,
                      ),
                ),
                const SizedBox(height: 14),
                FilledButton.icon(
                  key: const ValueKey('show-perspectives-button'),
                  onPressed: onShowPerspectives,
                  icon: const Icon(Icons.forum_outlined),
                  label: Text(strings.perspectiveDisclosureAction),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          PerspectiveSection(
            state: PerspectiveUiState.idle,
            result: null,
            reasonPendingModeration: state.reasonPendingModeration,
            onRetry: controller.retryPerspective,
          ),
          const SizedBox(height: 20),
          const ProgressSection(),
        ] else ...[
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
      ],
    );
  }
}

class _ProgressiveContextStep extends StatelessWidget {
  const _ProgressiveContextStep({
    required this.caseVersionId,
    required this.enabled,
    required this.onContinue,
  });

  final String caseVersionId;
  final bool enabled;
  final VoidCallback onContinue;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        ContextSection(caseVersionId: caseVersionId),
        const SizedBox(height: 14),
        Text(
          strings.contextAdvanceHelper,
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: context.kefeVisual.mutedForeground,
                height: 1.4,
              ),
        ),
        const SizedBox(height: 10),
        FilledButton.icon(
          key: const ValueKey('context-continue-button'),
          onPressed: enabled ? onContinue : null,
          icon: const Icon(Icons.arrow_forward_rounded),
          label: Text(strings.contextAdvanceAction),
        ),
        const SizedBox(height: 20),
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

class _JourneyUnavailableCard extends StatelessWidget {
  const _JourneyUnavailableCard({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Card(
      key: const ValueKey('active-journey-unavailable'),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Text(message),
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

IconData _iconForPrimitive(String primitiveCode) => switch (primitiveCode) {
  'CONTEXT' => Icons.article_outlined,
  'DECISION' => Icons.balance_rounded,
  'COLLECTIVE_RESULT' => Icons.insights_rounded,
  'REFLECTION' => Icons.route_rounded,
  _ => Icons.extension_outlined,
};
