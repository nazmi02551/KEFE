import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/design/kefe_theme.dart';
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
    await ref
        .read(decisionDraftStoreProvider)
        .write(
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
      final reusablePending =
          pending != null &&
          pending.caseVersionId == widget.caseVersionId &&
          pending.latestRevisionId == model.latestRevisionId;
      final idempotencyKey = reusablePending
          ? pending.idempotencyKey
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
        throw const ClientTransportFailure(
          code: 'FLOW_RUNTIME_VERSION_MISMATCH',
        );
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
    final completed =
        model?.completed == true ||
        widget.step.state == FlowStepRuntimeState.completed;

    return Card(
      key: ValueKey('reflection-step-${widget.step.code}'),
      child: Padding(
        padding: const EdgeInsets.all(18),
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
                    color: KefeColorTokens.gold.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(
                      color: KefeColorTokens.gold.withValues(alpha: 0.24),
                    ),
                  ),
                  child: const Icon(
                    Icons.route_rounded,
                    color: KefeColorTokens.goldSoft,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        strings.reflectionTitle,
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      if (model != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          strings.reflectionDecisionSummary(
                            model.decisionChanged,
                            model.changedQuestionCount,
                          ),
                          key: const ValueKey('reflection-summary'),
                          style: Theme.of(context).textTheme.bodySmall
                              ?.copyWith(
                                color: KefeColorTokens.textMutedDark,
                                height: 1.35,
                              ),
                        ),
                      ],
                    ],
                  ),
                ),
                if (model != null)
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 9,
                      vertical: 6,
                    ),
                    decoration: BoxDecoration(
                      color:
                          (model.decisionChanged
                                  ? KefeColorTokens.attention
                                  : KefeColorTokens.success)
                              .withValues(alpha: 0.10),
                      borderRadius: BorderRadius.circular(99),
                    ),
                    child: Icon(
                      model.decisionChanged
                          ? Icons.compare_arrows_rounded
                          : Icons.check_rounded,
                      size: 17,
                      color: model.decisionChanged
                          ? KefeColorTokens.attention
                          : KefeColorTokens.success,
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 16),
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
              _DecisionJourneyGraphic(model: model),
              if (model.interventionCount > 0) ...[
                const SizedBox(height: 14),
                Container(
                  key: const ValueKey('reflection-intervention-summary'),
                  padding: const EdgeInsets.all(13),
                  decoration: BoxDecoration(
                    color: KefeColorTokens.rules.withValues(alpha: 0.07),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(
                      color: KefeColorTokens.rules.withValues(alpha: 0.18),
                    ),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(
                        Icons.visibility_outlined,
                        color: KefeColorTokens.rules,
                        size: 20,
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          strings.reflectionInterventionSummary(
                            model.interventionCount,
                          ),
                          style: Theme.of(
                            context,
                          ).textTheme.bodyMedium?.copyWith(height: 1.4),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
              const SizedBox(height: 14),
              Container(
                padding: const EdgeInsets.all(13),
                decoration: BoxDecoration(
                  color: KefeColorTokens.surfaceElevatedDark.withValues(
                    alpha: 0.72,
                  ),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(
                    color: Theme.of(context).colorScheme.outlineVariant,
                  ),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(
                      Icons.info_outline_rounded,
                      color: KefeColorTokens.goldSoft,
                      size: 20,
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        strings.reflectionNonCausalNote,
                        key: const ValueKey('reflection-non-causal-note'),
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: KefeColorTokens.textMutedDark,
                          height: 1.45,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              if (_errorCode != null) ...[
                const SizedBox(height: 10),
                Text(
                  strings.messageForCode(_errorCode),
                  textAlign: TextAlign.center,
                ),
              ],
              const SizedBox(height: 16),
              if (completed)
                Container(
                  key: const ValueKey('reflection-completed'),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  decoration: BoxDecoration(
                    color: KefeColorTokens.success.withValues(alpha: 0.10),
                    borderRadius: BorderRadius.circular(13),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(
                        Icons.check_circle_rounded,
                        color: KefeColorTokens.success,
                        size: 19,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        strings.reflectionCompleted,
                        style: Theme.of(context).textTheme.labelLarge?.copyWith(
                          color: KefeColorTokens.success,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ],
                  ),
                )
              else
                FilledButton.icon(
                  key: const ValueKey('reflection-complete-button'),
                  onPressed: _completing ? null : _complete,
                  icon: _completing
                      ? const SizedBox.square(
                          dimension: 19,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.check_rounded),
                  label: Text(strings.reflectionComplete),
                ),
            ],
          ],
        ),
      ),
    );
  }
}

class _DecisionJourneyGraphic extends StatelessWidget {
  const _DecisionJourneyGraphic({required this.model});

  final ReflectionReadModel model;

  @override
  Widget build(BuildContext context) {
    final changedColor = model.decisionChanged
        ? KefeColorTokens.attention
        : KefeColorTokens.success;

    return Container(
      key: const ValueKey('reflection-journey-graphic'),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 16),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(18),
        gradient: LinearGradient(
          begin: Alignment.centerLeft,
          end: Alignment.centerRight,
          colors: [
            KefeColorTokens.rules.withValues(alpha: 0.08),
            KefeColorTokens.surfaceElevatedDark.withValues(alpha: 0.72),
            changedColor.withValues(alpha: 0.08),
          ],
        ),
        border: Border.all(color: KefeColorTokens.gold.withValues(alpha: 0.18)),
      ),
      child: Row(
        children: [
          _RevisionNode(
            label: '1',
            color: KefeColorTokens.rules,
            icon: Icons.balance_outlined,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Divider(
                        color: KefeColorTokens.gold.withValues(alpha: 0.32),
                      ),
                    ),
                    const SizedBox(width: 7),
                    Icon(
                      model.decisionChanged
                          ? Icons.swap_horiz_rounded
                          : Icons.arrow_forward_rounded,
                      color: changedColor,
                      size: 23,
                    ),
                    const SizedBox(width: 7),
                    Expanded(
                      child: Divider(
                        color: KefeColorTokens.gold.withValues(alpha: 0.32),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 7),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      Icons.visibility_outlined,
                      size: 14,
                      color: KefeColorTokens.textMutedDark,
                    ),
                    const SizedBox(width: 5),
                    Text(
                      '${model.interventionCount}',
                      style: Theme.of(context).textTheme.labelMedium?.copyWith(
                        color: KefeColorTokens.textMutedDark,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(width: 10),
          _RevisionNode(
            label: '${model.revisionCount}',
            color: changedColor,
            icon: model.decisionChanged
                ? Icons.change_circle_outlined
                : Icons.check_circle_outline_rounded,
          ),
        ],
      ),
    );
  }
}

class _RevisionNode extends StatelessWidget {
  const _RevisionNode({
    required this.label,
    required this.color,
    required this.icon,
  });

  final String label;
  final Color color;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 58,
      padding: const EdgeInsets.symmetric(vertical: 10),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withValues(alpha: 0.32)),
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 21),
          const SizedBox(height: 6),
          Text(
            label,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              color: color,
              fontWeight: FontWeight.w900,
            ),
          ),
        ],
      ),
    );
  }
}
