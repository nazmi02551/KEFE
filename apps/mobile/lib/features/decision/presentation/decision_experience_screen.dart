import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/config/experience_presentation_config.dart';
import '../../../core/design/kefe_active_journey.dart';
import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/design/product_preview_visual_mode.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../community_reason/presentation/community_reason_section.dart';
import '../../consensus/presentation/consensus_section.dart';
import '../../context/presentation/context_section.dart';
import '../../onboarding/application/onboarding_controller.dart';
import '../../progress/presentation/progress_section.dart';
import '../../sharing/presentation/share_section.dart';
import '../application/decision_controller.dart';
import '../domain/decision_models.dart';
import 'case_hero_header.dart';
import 'decision_flow_screen.dart';
import 'decision_journey_stage_resolver.dart';
import 'decision_journey_strings.dart';
import 'perspective_section.dart';
import 'question_input.dart';
import 'reason_input.dart';
import 'reflection_step.dart';
import 'reveal_result_card.dart';

class DecisionExperienceScreen extends ConsumerWidget {
  const DecisionExperienceScreen({
    required this.caseId,
    this.firstUse = false,
    super.key,
  });

  final String caseId;
  final bool firstUse;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final experience = ref.watch(experiencePresentationConfigProvider);
    if (experience.decisionJourneyMode ==
        DecisionJourneyPresentationMode.legacyLongScroll) {
      return DecisionFlowScreen(caseId: caseId, firstUse: firstUse);
    }
    return _ProgressiveDecisionFlowScreen(caseId: caseId, firstUse: firstUse);
  }
}

class _ProgressiveDecisionFlowScreen extends ConsumerStatefulWidget {
  const _ProgressiveDecisionFlowScreen({
    required this.caseId,
    required this.firstUse,
  });

  final String caseId;
  final bool firstUse;

  @override
  ConsumerState<_ProgressiveDecisionFlowScreen> createState() =>
      _ProgressiveDecisionFlowScreenState();
}

class _ProgressiveDecisionFlowScreenState
    extends ConsumerState<_ProgressiveDecisionFlowScreen> {
  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void didUpdateWidget(covariant _ProgressiveDecisionFlowScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.caseId != widget.caseId) _load();
  }

  void _load() {
    Future<void>.microtask(
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
              ? _JourneyLoadingState(
                  key: const ValueKey('loading'),
                  label: strings.loading,
                )
              : state.caseData == null || state.flowRuntime == null
              ? _JourneyErrorState(
                  key: const ValueKey('error'),
                  message: strings.messageForCode(state.errorCode),
                  retryLabel: strings.retry,
                  onRetry: _load,
                )
              : _ProgressiveDecisionContent(
                  key: ValueKey('progressive-content-${state.caseData!.id}'),
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
    final previousRuntime = oldWidget.state.flowRuntime;
    final nextRuntime = widget.state.flowRuntime;
    final previousStep = previousRuntime == null
        ? null
        : DecisionJourneyStageResolver.primary(previousRuntime);
    final nextStep = nextRuntime == null
        ? null
        : DecisionJourneyStageResolver.primary(nextRuntime);
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
    final runtime = state.flowRuntime!;
    final productPreviewVisual = ref.watch(productPreviewVisualModeProvider);
    final activeStep = DecisionJourneyStageResolver.primary(runtime);

    return ListView(
      key: const ValueKey('progressive-decision-journey'),
      padding: const EdgeInsets.all(20),
      children: [
        if (productPreviewVisual)
          CaseHeroHeader(caseData: caseData, flowRuntime: runtime)
        else
          _JourneyCaseHeader(caseData: caseData),
        const SizedBox(height: 20),
        if (activeStep == null)
          _JourneyMessageSurface(
            key: const ValueKey('active-journey-unavailable'),
            message: strings.activeJourneyUnavailable,
          )
        else
          KefeActiveJourney(
            stageId: activeStep.code,
            eyebrow: strings.activeJourneyEyebrow,
            title: strings.activeJourneyTitle(activeStep.primitiveCode),
            subtitle: strings.activeJourneyHelper,
            progressLabel: strings.activeJourneyProgress(
              DecisionJourneyStageResolver.ordinal(runtime, activeStep),
              runtime.steps.length,
            ),
            icon: _iconForPrimitive(activeStep.primitiveCode),
            child: _ActiveFlowStep(
              key: ValueKey('active-flow-step-${activeStep.code}'),
              step: activeStep,
              state: state,
              firstUse: widget.firstUse,
              showPerspectives: _showPerspectives,
              onShowPerspectives: () {
                setState(() => _showPerspectives = true);
              },
            ),
          ),
        if (state.errorCode != null) ...[
          const SizedBox(height: 16),
          _JourneyStatusSurface(
            message: strings.messageForCode(state.errorCode),
            offlineDraft: state.offlineDraft,
          ),
        ],
      ],
    );
  }
}

IconData _iconForPrimitive(String primitiveCode) => switch (primitiveCode) {
  'CONTEXT' => Icons.menu_book_rounded,
  'DECISION' => Icons.balance_rounded,
  'COLLECTIVE_RESULT' => Icons.groups_2_rounded,
  'REFLECTION' => Icons.route_rounded,
  _ => Icons.auto_awesome_rounded,
};

class _ActiveFlowStep extends ConsumerWidget {
  const _ActiveFlowStep({
    required this.step,
    required this.state,
    required this.firstUse,
    required this.showPerspectives,
    required this.onShowPerspectives,
    super.key,
  });

  final FlowRuntimeStep step;
  final DecisionState state;
  final bool firstUse;
  final bool showPerspectives;
  final VoidCallback onShowPerspectives;

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
      _ => _JourneyMessageSurface(
        message: KefeStrings.of(
          context,
        ).flowCapabilityPendingBody(step.reasonCode),
      ),
    };
  }

  Widget _contextStep(BuildContext context, WidgetRef ref) {
    if (step.state == FlowStepRuntimeState.unsupported) {
      return _JourneyMessageSurface(
        message: KefeStrings.of(
          context,
        ).flowCapabilityPendingBody(step.reasonCode),
      );
    }
    if (step.state != FlowStepRuntimeState.ready) {
      return _JourneyMessageSurface(
        message: KefeStrings.of(context).activeJourneyUnavailable,
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        ContextSection(caseVersionId: state.caseData!.versionId),
        const SizedBox(height: 16),
        _ContextAdvancePanel(
          enabled: !state.offlineDraft && !state.submitting,
          onContinue: () => ref
              .read(decisionControllerProvider.notifier)
              .recordContextExposure(step.code),
        ),
      ],
    );
  }

  Widget _decisionStep(BuildContext context, WidgetRef ref) {
    if (step.state == FlowStepRuntimeState.unsupported) {
      return _JourneyMessageSurface(
        message: KefeStrings.of(
          context,
        ).flowCapabilityPendingBody(step.reasonCode),
      );
    }
    if (step.state != FlowStepRuntimeState.ready) {
      return _JourneyMessageSurface(
        message: KefeStrings.of(context).activeJourneyUnavailable,
      );
    }

    final caseData = state.caseData!;
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
        if (caseData.reasonPolicy != null) ...[
          ReasonInputCard(
            policy: caseData.reasonPolicy!,
            selectedTags: state.reasonTags,
            text: state.reasonText,
            enabled: inputsEnabled,
            onTagToggled: controller.toggleReasonTag,
            onTextChanged: controller.setReasonText,
          ),
          const SizedBox(height: 12),
        ],
        const SizedBox(height: 8),
        _JourneyCommitPanel(
          onPressed: action,
          submitting: state.submitting,
          recoveryPending: state.recoveryPending,
          hasRequiredResponses: state.hasRequiredResponses,
        ),
      ],
    );
  }

  Widget _reflectionStep() {
    if (step.state == FlowStepRuntimeState.unsupported) {
      return _JourneyMessageSurface(message: step.reasonCode ?? 'REFLECTION');
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
      return _JourneyMessageSurface(
        message: KefeStrings.of(
          context,
        ).flowCapabilityPendingBody(step.reasonCode),
      );
    }
    if (step.state != FlowStepRuntimeState.ready || state.reveal == null) {
      return const SizedBox.shrink();
    }

    final controller = ref.read(decisionControllerProvider.notifier);
    final sessionId = state.sessionId!;
    final caseVersionId = state.caseData!.versionId;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        RevealResultCard(
          reveal: state.reveal!,
          selectedOption: state.selectedOption,
        ),
        const SizedBox(height: 18),
        if (!showPerspectives) ...[
          _PerspectiveDisclosurePanel(onPressed: onShowPerspectives),
          const SizedBox(height: 20),
          ConsensusSection(sessionId: sessionId, caseVersionId: caseVersionId),
          const SizedBox(height: 20),
          CommunityReasonSection(
            sessionId: sessionId,
            caseVersionId: caseVersionId,
          ),
          const SizedBox(height: 20),
          const ProgressSection(),
          const SizedBox(height: 20),
          ShareSection(sessionId: sessionId),
        ] else ...[
          PerspectiveSection(
            state: state.perspectiveState,
            result: state.perspective,
            reasonPendingModeration: state.reasonPendingModeration,
            onRetry: controller.retryPerspective,
          ),
          if (firstUse) ...[
            const SizedBox(height: 20),
            _JourneyFirstUseCompletion(
              onContinue: () => context.go('/explore'),
            ),
          ],
        ],
      ],
    );
  }
}

class _JourneyCaseHeader extends StatelessWidget {
  const _JourneyCaseHeader({required this.caseData});

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

class _ContextAdvancePanel extends StatelessWidget {
  const _ContextAdvancePanel({required this.enabled, required this.onContinue});

  final bool enabled;
  final VoidCallback onContinue;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    return KefeSurface(
      key: const ValueKey('context-advance-panel'),
      tone: KefeSurfaceTone.raised,
      accent: visual.rules,
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            strings.contextAdvanceHelper,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: visual.mutedForeground,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 12),
          FilledButton.icon(
            key: const ValueKey('context-continue-button'),
            onPressed: enabled ? onContinue : null,
            icon: const Icon(Icons.arrow_forward_rounded),
            label: Text(strings.contextAdvanceAction),
          ),
        ],
      ),
    );
  }
}

class _PerspectiveDisclosurePanel extends StatelessWidget {
  const _PerspectiveDisclosurePanel({required this.onPressed});

  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    return KefeSurface(
      key: const ValueKey('perspective-disclosure-prompt'),
      tone: KefeSurfaceTone.raised,
      accent: visual.rules,
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            strings.perspectiveDisclosureTitle,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              color: visual.foreground,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            strings.perspectiveDisclosureBody,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: visual.mutedForeground,
              height: 1.42,
            ),
          ),
          const SizedBox(height: 14),
          FilledButton.icon(
            key: const ValueKey('show-perspectives-button'),
            onPressed: onPressed,
            icon: const Icon(Icons.forum_outlined),
            label: Text(strings.perspectiveDisclosureAction),
          ),
        ],
      ),
    );
  }
}

class _JourneyCommitPanel extends StatelessWidget {
  const _JourneyCommitPanel({
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

class _JourneyStatusSurface extends StatelessWidget {
  const _JourneyStatusSurface({
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

class _JourneyMessageSurface extends StatelessWidget {
  const _JourneyMessageSurface({required this.message, super.key});

  final String message;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return KefeSurface(
      tone: KefeSurfaceTone.raised,
      accent: visual.attention,
      padding: const EdgeInsets.all(18),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ExcludeSemantics(
            child: Icon(Icons.info_outline_rounded, color: visual.attention),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              message,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: visual.foreground,
                height: 1.42,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _JourneyLoadingState extends StatelessWidget {
  const _JourneyLoadingState({required this.label, super.key});

  final String label;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: KefeSurface(
          tone: KefeSurfaceTone.raised,
          accent: visual.gold,
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
          child: Semantics(
            liveRegion: true,
            label: label,
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.hourglass_top_rounded, color: visual.goldSoft),
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

class _JourneyErrorState extends StatelessWidget {
  const _JourneyErrorState({
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
        child: KefeSurface(
          tone: KefeSurfaceTone.raised,
          accent: Theme.of(context).colorScheme.error,
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Icon(
                Icons.error_outline_rounded,
                color: Theme.of(context).colorScheme.error,
                size: 30,
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
    );
  }
}

class _JourneyFirstUseCompletion extends StatelessWidget {
  const _JourneyFirstUseCompletion({required this.onContinue});

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
            children: [
              Icon(Icons.check_rounded, color: visual.success, size: 28),
              const SizedBox(width: 12),
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
