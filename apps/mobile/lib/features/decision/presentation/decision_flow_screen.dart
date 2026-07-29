import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/kefe_strings.dart';
import '../../context/presentation/context_section.dart';
import '../../onboarding/application/onboarding_controller.dart';
import '../application/decision_controller.dart';
import '../data/decision_repository.dart';
import '../domain/decision_models.dart';
import '../domain/reflection_models.dart';
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
      'CONTEXT' => _contextStep(ref),
      'DECISION' => _decisionStep(context, ref),
      'COLLECTIVE_RESULT' => _resultStep(context, ref),
      'REFLECTION' => _reflectionStep(),
      _ => step.state == FlowStepRuntimeState.unsupported
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

  Widget _reflectionStep() {
    if (step.state == FlowStepRuntimeState.unsupported) {
      return _CapabilityPendingCard(step: step);
    }
    if (step.state != FlowStepRuntimeState.ready &&
        step.state != FlowStepRuntimeState.completed) {
      return const SizedBox.shrink();
    }
    return _ReflectionStep(
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
          _FirstUseCompletionCard(
            onContinue: () => context.go('/explore'),
          ),
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

class _ReflectionStep extends ConsumerStatefulWidget {
  const _ReflectionStep({
    required this.sessionId,
    required this.caseVersionId,
    required this.step,
  });

  final String sessionId;
  final String caseVersionId;
  final FlowRuntimeStep step;

  @override
  ConsumerState<_ReflectionStep> createState() => _ReflectionStepState();
}

class _ReflectionStepState extends ConsumerState<_ReflectionStep> {
  ReflectionReadModel? _model;
  FlowStepRuntimeState? _runtimeState;
  bool _loading = false;
  bool _completing = false;
  String? _errorCode;

  @override
  void initState() {
    super.initState();
    _scheduleLoad();
  }

  @override
  void didUpdateWidget(covariant _ReflectionStep oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.sessionId != widget.sessionId ||
        oldWidget.caseVersionId != widget.caseVersionId ||
        oldWidget.step.code != widget.step.code ||
        oldWidget.step.state != widget.step.state) {
      _model = null;
      _runtimeState = null;
      _scheduleLoad();
    }
  }

  void _scheduleLoad() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _load();
    });
  }

  Future<void> _load() async {
    if (_loading) return;
    setState(() {
      _loading = true;
      _errorCode = null;
    });
    try {
      final model = await ref.read(decisionRepositoryProvider).reflection.fetchReflection(
        sessionId: widget.sessionId,
        stepCode: widget.step.code,
      );
      if (!mounted) return;
      setState(() {
        _model = model;
        _loading = false;
      });
    } on ClientTransportFailure catch (error) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _errorCode = error.code;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _errorCode = 'UNEXPECTED_CLIENT_ERROR';
      });
    }
  }

  Future<void> _complete() async {
    final model = _model;
    if (model == null || _isCompleted || _completing) return;
    setState(() {
      _completing = true;
      _errorCode = null;
    });
    try {
      final repository = ref.read(decisionRepositoryProvider);
      await repository.reflection.completeReflection(
        sessionId: widget.sessionId,
        stepCode: widget.step.code,
        idempotencyKey:
            'mobile-reflection-${widget.sessionId}-${widget.step.code}-${model.latestRevisionId}-v1',
      );
      final refreshed = await repository.fetchFlowRuntime(widget.sessionId);
      if (!refreshed.matches(
        sessionId: widget.sessionId,
        caseVersionId: widget.caseVersionId,
      )) {
        throw const ClientTransportFailure(code: 'FLOW_RUNTIME_VERSION_MISMATCH');
      }
      FlowRuntimeStep? refreshedStep;
      for (final item in refreshed.steps) {
        if (item.code == widget.step.code && item.primitiveCode == 'REFLECTION') {
          refreshedStep = item;
          break;
        }
      }
      final refreshedModel = await repository.reflection.fetchReflection(
        sessionId: widget.sessionId,
        stepCode: widget.step.code,
      );
      if (!mounted) return;
      setState(() {
        _model = refreshedModel;
        _runtimeState = refreshedStep?.state;
        _completing = false;
      });
    } on ClientTransportFailure catch (error) {
      if (!mounted) return;
      setState(() {
        _completing = false;
        _errorCode = error.code;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _completing = false;
        _errorCode = 'UNEXPECTED_CLIENT_ERROR';
      });
    }
  }

  bool get _isCompleted =>
      _model?.completed == true ||
      _runtimeState == FlowStepRuntimeState.completed ||
      widget.step.state == FlowStepRuntimeState.completed;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final model = _model;
    return Card(
      key: ValueKey('reflection-step-${widget.step.code}'),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              strings.reflectionTitle,
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 12),
            if (_loading && model == null)
              Text(strings.reflectionLoading)
            else if (_errorCode != null && model == null) ...[
              Text(strings.messageForCode(_errorCode)),
              const SizedBox(height: 12),
              OutlinedButton(
                key: const ValueKey('reflection-retry'),
                onPressed: _load,
                child: Text(strings.reflectionRetry),
              ),
            ] else if (model != null) ...[
              Text(
                strings.reflectionDecisionSummary(
                  model.decisionChanged,
                  model.changedQuestionCount,
                ),
                key: const ValueKey('reflection-summary'),
              ),
              if (model.interventionCount > 0) ...[
                const SizedBox(height: 8),
                Text(
                  strings.reflectionInterventionSummary(model.interventionCount),
                ),
              ],
              const SizedBox(height: 8),
              Text(
                strings.reflectionNonCausalNote,
                key: const ValueKey('reflection-non-causal-note'),
              ),
              if (_errorCode != null) ...[
                const SizedBox(height: 8),
                Text(
                  strings.messageForCode(_errorCode),
                  textAlign: TextAlign.center,
                ),
              ],
              const SizedBox(height: 16),
              if (_isCompleted)
                Text(
                  strings.reflectionCompleted,
                  key: const ValueKey('reflection-completed'),
                  textAlign: TextAlign.center,
                )
              else
                FilledButton(
                  key: const ValueKey('reflection-complete-button'),
                  onPressed: _completing ? null : _complete,
                  child: _completing
                      ? const SizedBox.square(
                          dimension: 22,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : Text(strings.reflectionComplete),
                ),
            ],
          ],
        ),
      ),
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
