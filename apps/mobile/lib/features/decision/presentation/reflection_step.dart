import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/localization/kefe_strings.dart';
import '../application/decision_controller.dart';
import '../application/reflection_completion_provider.dart';
import '../data/decision_repository.dart';
import '../data/reflection_completion_store.dart';
import '../domain/decision_draft.dart';
import '../domain/decision_models.dart';
import '../domain/reflection_models.dart';

class ReflectionStepCard extends ConsumerStatefulWidget {
  const ReflectionStepCard({
    required this.sessionId,
    required this.caseVersionId,
    required this.step,
    super.key,
  });

  final String sessionId;
  final String caseVersionId;
  final FlowRuntimeStep step;

  @override
  ConsumerState<ReflectionStepCard> createState() => _ReflectionStepCardState();
}

class _ReflectionStepCardState extends ConsumerState<ReflectionStepCard> {
  ReflectionReadModel? _model;
  bool _loading = false;
  bool _completing = false;
  String? _errorCode;

  @override
  void initState() {
    super.initState();
    _scheduleLoad();
  }

  @override
  void didUpdateWidget(covariant ReflectionStepCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.sessionId != widget.sessionId ||
        oldWidget.caseVersionId != widget.caseVersionId ||
        oldWidget.step.code != widget.step.code ||
        oldWidget.step.state != widget.step.state) {
      _model = null;
      _scheduleLoad();
    }
  }

  ReflectionCompletionStore get _completionStore =>
      ref.read(reflectionCompletionStoreProvider);

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
      final model = await ref
          .read(decisionRepositoryProvider)
          .reflection
          .fetchReflection(
            sessionId: widget.sessionId,
            stepCode: widget.step.code,
          );
      await _reconcilePendingCompletion(model);
      if (!model.completed) {
        await _persistFlowRecoveryDraft();
      }
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

  Future<void> _reconcilePendingCompletion(ReflectionReadModel model) async {
    final pending = await _completionStore.read(
      sessionId: widget.sessionId,
      stepCode: widget.step.code,
    );
    if (pending == null) return;
    if (model.completed ||
        pending.caseVersionId != widget.caseVersionId ||
        pending.latestRevisionId != model.latestRevisionId) {
      await _completionStore.clear(
        sessionId: widget.sessionId,
        stepCode: widget.step.code,
      );
    }
  }

  Future<void> _persistFlowRecoveryDraft() async {
    final decisionState = ref.read(decisionControllerProvider);
    final caseData = decisionState.caseData;
    final flowRuntime = decisionState.flowRuntime;
    if (caseData == null ||
        flowRuntime == null ||
        decisionState.sessionId != widget.sessionId ||
        caseData.versionId != widget.caseVersionId) {
      return;
    }
    await ref.read(decisionDraftStoreProvider).write(
      DecisionDraft(
        caseData: caseData,
        sessionId: widget.sessionId,
        flowRuntime: flowRuntime,
        updatedAt: DateTime.now().toUtc(),
      ),
    );
  }

  Future<void> _complete() async {
    final model = _model;
    if (model == null || model.completed || _completing) return;
    setState(() {
      _completing = true;
      _errorCode = null;
    });
    try {
      final pending = await _completionStore.read(
        sessionId: widget.sessionId,
        stepCode: widget.step.code,
      );
      final reusablePending = pending != null &&
          pending.caseVersionId == widget.caseVersionId &&
          pending.latestRevisionId == model.latestRevisionId;
      final idempotencyKey = reusablePending
          ? pending!.idempotencyKey
          : 'mobile-reflection-${widget.sessionId}-${widget.step.code}-${model.latestRevisionId}-v1';
      if (!reusablePending) {
        await _completionStore.write(
          PendingReflectionCompletion(
            sessionId: widget.sessionId,
            caseVersionId: widget.caseVersionId,
            stepCode: widget.step.code,
            latestRevisionId: model.latestRevisionId,
            idempotencyKey: idempotencyKey,
          ),
        );
      }
      await _persistFlowRecoveryDraft();

      final repository = ref.read(decisionRepositoryProvider);
      await repository.reflection.completeReflection(
        sessionId: widget.sessionId,
        stepCode: widget.step.code,
        idempotencyKey: idempotencyKey,
      );
      final refreshed = await repository.fetchFlowRuntime(widget.sessionId);
      if (!refreshed.matches(
        sessionId: widget.sessionId,
        caseVersionId: widget.caseVersionId,
      )) {
        throw const ClientTransportFailure(code: 'FLOW_RUNTIME_VERSION_MISMATCH');
      }
      final refreshedModel = await repository.reflection.fetchReflection(
        sessionId: widget.sessionId,
        stepCode: widget.step.code,
      );
      if (refreshedModel.completed) {
        await _completionStore.clear(
          sessionId: widget.sessionId,
          stepCode: widget.step.code,
        );
      }
      if (mounted) {
        setState(() {
          _model = refreshedModel;
          _completing = false;
        });
      }
      await _adoptRefreshedFlow(refreshed);
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

  Future<void> _adoptRefreshedFlow(FlowRuntimeSnapshot refreshed) async {
    final decisionState = ref.read(decisionControllerProvider);
    final caseData = decisionState.caseData;
    if (caseData == null ||
        decisionState.sessionId != widget.sessionId ||
        caseData.versionId != widget.caseVersionId) {
      return;
    }

    FlowRuntimeStep? nextDecision;
    for (final item in refreshed.steps) {
      if (item.primitiveCode == 'DECISION' &&
          item.state == FlowStepRuntimeState.ready) {
        nextDecision = item;
        break;
      }
    }
    final flowTerminal = refreshed.steps.every(
      (item) =>
          item.state == FlowStepRuntimeState.completed ||
          item.state == FlowStepRuntimeState.unsupported,
    );

    final draftStore = ref.read(decisionDraftStoreProvider);
    await draftStore.write(
      DecisionDraft(
        caseData: caseData,
        sessionId: widget.sessionId,
        flowRuntime: refreshed,
        flowStepCode: nextDecision?.code,
        updatedAt: DateTime.now().toUtc(),
      ),
    );
    await ref.read(decisionControllerProvider.notifier).load(caseData.id);
    final adopted = ref.read(decisionControllerProvider);
    if (flowTerminal && !adopted.offlineDraft && adopted.errorCode == null) {
      await draftStore.clearForCase(caseData.id);
    }
  }

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final model = _model;
    final completed = model?.completed == true ||
        widget.step.state == FlowStepRuntimeState.completed;
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
              if (completed)
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
