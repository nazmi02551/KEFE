import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/kefe_strings.dart';
import '../../context/presentation/context_section.dart';
import '../../onboarding/application/onboarding_controller.dart';
import '../application/decision_controller.dart';
import '../domain/decision_models.dart';
import 'perspective_section.dart';
import 'question_input.dart';
import 'reason_input.dart';

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

    ref.listen<DecisionState>(decisionControllerProvider, (previous, next) async {
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

    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Text(
          caseData.title,
          key: const ValueKey('case-title'),
          style: Theme.of(context).textTheme.headlineMedium,
        ),
        const SizedBox(height: 12),
        Text(caseData.summary, style: Theme.of(context).textTheme.bodyLarge),
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
      'CONTEXT' => _contextStep(),
      'DECISION' => _decisionStep(context, ref),
      'COLLECTIVE_RESULT' => _resultStep(context, ref),
      _ => step.state == FlowStepRuntimeState.unsupported
          ? _CapabilityPendingCard(step: step)
          : const SizedBox.shrink(),
    };
  }

  Widget _contextStep() {
    if (step.state != FlowStepRuntimeState.ready &&
        step.state != FlowStepRuntimeState.completed) {
      return const SizedBox.shrink();
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        ContextSection(caseVersionId: state.caseData!.versionId),
        const SizedBox(height: 24),
      ],
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
    final inputsEnabled =
        !state.recoveryPending && !state.submitting && state.reveal == null;

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
              : Text(state.recoveryPending ? strings.retrySync : strings.commit),
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
          _FirstUseCompletionCard(
            onContinue: () => context.go('/explore'),
          ),
        ],
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
    return Card(
      key: const ValueKey('reveal-card'),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              strings.revealTitle,
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 12),
            for (final entry in reveal.values.entries)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('${entry.key} · ${(entry.value * 100).round()}%'),
                    const SizedBox(height: 6),
                    LinearProgressIndicator(value: entry.value),
                  ],
                ),
              ),
            const SizedBox(height: 8),
            Text(
              '${strings.trustedSample} · '
              'n=${reveal.sampleSize} · ${reveal.confidence}',
              key: const ValueKey('reveal-methodology'),
            ),
          ],
        ),
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
