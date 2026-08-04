part of 'decision_experience_screen.dart';

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
      'CONTEXT' => _contextStep(context, ref),
      'DECISION' => _decisionStep(context, ref),
      'COLLECTIVE_RESULT' => _resultStep(context),
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
        ContextSection(
          caseVersionId: state.caseData!.versionId,
          progressive: true,
        ),
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

    return DecisionSubjourney(
      key: ValueKey('decision-subjourney-${step.code}'),
      caseData: caseData,
      flowStepCode: step.code,
      responses: state.responses,
      selectedReasonTags: state.reasonTags,
      reasonText: state.reasonText,
      enabled: inputsEnabled,
      onResponseChanged: controller.setResponse,
      onReasonTagToggled: controller.toggleReasonTag,
      onReasonTextChanged: controller.setReasonText,
      reviewAction: _JourneyCommitPanel(
        onPressed: action,
        submitting: state.submitting,
        recoveryPending: state.recoveryPending,
        hasRequiredResponses: state.hasRequiredResponses,
      ),
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

  Widget _resultStep(BuildContext context) {
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

    return PostCommitJourney(
      state: state,
      sessionId: state.sessionId!,
      caseVersionId: state.caseData!.versionId,
      completionAction: firstUse
          ? _JourneyFirstUseCompletion(
              onContinue: () => context.go('/explore'),
            )
          : null,
    );
  }
}
