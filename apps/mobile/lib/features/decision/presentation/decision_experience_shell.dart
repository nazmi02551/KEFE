part of 'decision_experience_screen.dart';

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
            title: strings.activeJourneyTitle(
              activeStep.primitiveCode,
              repeatedDecision: DecisionJourneyStageResolver.isRepeatedDecision(
                runtime,
                activeStep,
              ),
            ),
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
