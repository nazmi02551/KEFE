import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/kefe_content_localizer.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/decision_models.dart';
import 'decision_journey_strings.dart';
import 'question_input.dart';
import 'reason_input.dart';

enum DecisionSubjourneyStageKind { question, reason, review }

@immutable
class DecisionSubjourneyStage {
  const DecisionSubjourneyStage._({
    required this.id,
    required this.kind,
    this.question,
  });

  factory DecisionSubjourneyStage.question(DecisionQuestion question) =>
      DecisionSubjourneyStage._(
        id: question.id,
        kind: DecisionSubjourneyStageKind.question,
        question: question,
      );

  const DecisionSubjourneyStage.reason()
    : this._(id: 'reason', kind: DecisionSubjourneyStageKind.reason);

  const DecisionSubjourneyStage.review()
    : this._(id: 'review', kind: DecisionSubjourneyStageKind.review);

  final String id;
  final DecisionSubjourneyStageKind kind;
  final DecisionQuestion? question;
}

abstract final class DecisionSubjourneyResolver {
  static List<DecisionSubjourneyStage> stages(DecisionCase caseData) => [
    for (final question in caseData.questions)
      DecisionSubjourneyStage.question(question),
    if (caseData.reasonPolicy != null) const DecisionSubjourneyStage.reason(),
    const DecisionSubjourneyStage.review(),
  ];

  static int initialIndex({
    required DecisionCase caseData,
    required Map<String, Object?> responses,
    Set<String> skippedQuestionIds = const {},
  }) {
    final resolved = stages(caseData);
    for (var index = 0; index < resolved.length; index += 1) {
      final stage = resolved[index];
      final question = stage.question;
      if (question != null &&
          question.required &&
          !responses.containsKey(question.id)) {
        return index;
      }
    }
    for (var index = 0; index < resolved.length; index += 1) {
      final question = resolved[index].question;
      if (question != null &&
          !responses.containsKey(question.id) &&
          !skippedQuestionIds.contains(question.id)) {
        return index;
      }
    }
    final reasonIndex = resolved.indexWhere(
      (stage) => stage.kind == DecisionSubjourneyStageKind.reason,
    );
    return reasonIndex >= 0 ? reasonIndex : resolved.length - 1;
  }
}

class DecisionSubjourney extends ConsumerStatefulWidget {
  const DecisionSubjourney({
    required this.caseData,
    required this.flowStepCode,
    required this.responses,
    required this.selectedReasonTags,
    required this.reasonText,
    required this.enabled,
    required this.onResponseChanged,
    required this.onReasonTagToggled,
    required this.onReasonTextChanged,
    required this.reviewAction,
    super.key,
  });

  final DecisionCase caseData;
  final String flowStepCode;
  final Map<String, Object?> responses;
  final Set<String> selectedReasonTags;
  final String reasonText;
  final bool enabled;
  final Future<void> Function(String questionId, Object value)
  onResponseChanged;
  final Future<void> Function(String tag) onReasonTagToggled;
  final Future<void> Function(String value) onReasonTextChanged;
  final Widget reviewAction;

  @override
  ConsumerState<DecisionSubjourney> createState() => _DecisionSubjourneyState();
}

class _DecisionSubjourneyState extends ConsumerState<DecisionSubjourney> {
  late List<DecisionSubjourneyStage> _stages;
  late int _activeIndex;
  final Set<String> _skippedQuestionIds = {};

  @override
  void initState() {
    super.initState();
    _reset();
  }

  @override
  void didUpdateWidget(covariant DecisionSubjourney oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.caseData.versionId != widget.caseData.versionId ||
        oldWidget.flowStepCode != widget.flowStepCode) {
      _skippedQuestionIds.clear();
      _reset();
    } else {
      _stages = DecisionSubjourneyResolver.stages(widget.caseData);
      _activeIndex = _activeIndex.clamp(0, _stages.length - 1);
    }
  }

  void _reset() {
    _stages = DecisionSubjourneyResolver.stages(widget.caseData);
    _activeIndex = DecisionSubjourneyResolver.initialIndex(
      caseData: widget.caseData,
      responses: widget.responses,
      skippedQuestionIds: _skippedQuestionIds,
    );
  }

  DecisionSubjourneyStage get _activeStage => _stages[_activeIndex];

  void _back() {
    if (_activeIndex == 0) return;
    setState(() => _activeIndex -= 1);
  }

  void _nextQuestion() {
    final question = _activeStage.question!;
    final answered = widget.responses.containsKey(question.id);
    if (question.required && !answered) return;
    setState(() {
      if (!answered) {
        _skippedQuestionIds.add(question.id);
      } else {
        _skippedQuestionIds.remove(question.id);
      }
      _activeIndex = (_activeIndex + 1).clamp(0, _stages.length - 1);
    });
  }

  void _next() {
    setState(
      () => _activeIndex = (_activeIndex + 1).clamp(0, _stages.length - 1),
    );
  }

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final stage = _activeStage;
    return Column(
      key: const ValueKey('decision-subjourney'),
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _DecisionSubjourneyHeader(
          stage: stage,
          current: _activeIndex + 1,
          total: _stages.length,
        ),
        const SizedBox(height: 14),
        AnimatedSwitcher(
          duration: KefeMotion.resolve(
            context,
            const Duration(milliseconds: 220),
          ),
          child: KeyedSubtree(
            key: ValueKey('decision-substage-${stage.id}'),
            child: switch (stage.kind) {
              DecisionSubjourneyStageKind.question => _questionStage(stage),
              DecisionSubjourneyStageKind.reason => _reasonStage(),
              DecisionSubjourneyStageKind.review => _reviewStage(),
            },
          ),
        ),
        const SizedBox(height: 14),
        if (stage.kind != DecisionSubjourneyStageKind.review)
          _DecisionSubjourneyNavigation(
            showBack: _activeIndex > 0,
            onBack: _back,
            onNext: stage.kind == DecisionSubjourneyStageKind.question
                ? _questionCanContinue(stage.question!)
                      ? _nextQuestion
                      : null
                : _next,
            nextLabel:
                stage.kind == DecisionSubjourneyStageKind.question &&
                    !stage.question!.required &&
                    !widget.responses.containsKey(stage.question!.id)
                ? strings.decisionJourneySkip
                : strings.decisionJourneyNext,
          ),
      ],
    );
  }

  bool _questionCanContinue(DecisionQuestion question) =>
      !question.required || widget.responses.containsKey(question.id);

  Widget _questionStage(DecisionSubjourneyStage stage) {
    final question = stage.question!;
    return QuestionInputCard(
      question: question,
      value: widget.responses[question.id],
      enabled: widget.enabled,
      onChanged: (value) {
        _skippedQuestionIds.remove(question.id);
        widget.onResponseChanged(question.id, value);
      },
    );
  }

  Widget _reasonStage() {
    final policy = widget.caseData.reasonPolicy!;
    return ReasonInputCard(
      policy: policy,
      selectedTags: widget.selectedReasonTags,
      text: widget.reasonText,
      enabled: widget.enabled,
      onTagToggled: widget.onReasonTagToggled,
      onTextChanged: widget.onReasonTextChanged,
    );
  }

  Widget _reviewStage() => _DecisionReviewStage(
    caseData: widget.caseData,
    responses: widget.responses,
    selectedReasonTags: widget.selectedReasonTags,
    reasonText: widget.reasonText,
    onBack: _activeIndex > 0 ? _back : null,
    reviewAction: widget.reviewAction,
  );
}

class _DecisionSubjourneyHeader extends StatelessWidget {
  const _DecisionSubjourneyHeader({
    required this.stage,
    required this.current,
    required this.total,
  });

  final DecisionSubjourneyStage stage;
  final int current;
  final int total;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final title = switch (stage.kind) {
      DecisionSubjourneyStageKind.question =>
        strings.decisionJourneyQuestionTitle(current, total),
      DecisionSubjourneyStageKind.reason => strings.decisionJourneyReasonTitle,
      DecisionSubjourneyStageKind.review => strings.decisionJourneyReviewTitle,
    };
    final icon = switch (stage.kind) {
      DecisionSubjourneyStageKind.question => Icons.balance_rounded,
      DecisionSubjourneyStageKind.reason => Icons.psychology_alt_outlined,
      DecisionSubjourneyStageKind.review => Icons.fact_check_outlined,
    };
    return KefeSurface(
      key: const ValueKey('decision-subjourney-header'),
      tone: KefeSurfaceTone.sunken,
      accent: visual.gold,
      padding: const EdgeInsets.all(15),
      borderRadius: 19,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Icon(icon, color: visual.goldSoft, size: 21),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  title,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: visual.onSurfaceStrong,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
              Text(
                strings.decisionJourneyProgress(current, total),
                style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  color: visual.goldSoft,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ClipRRect(
            borderRadius: BorderRadius.circular(99),
            child: LinearProgressIndicator(
              key: const ValueKey('decision-subjourney-progress'),
              value: current / total,
              minHeight: 6,
              backgroundColor: visual.border.withValues(alpha: 0.45),
              color: visual.gold,
            ),
          ),
        ],
      ),
    );
  }
}

class _DecisionSubjourneyNavigation extends StatelessWidget {
  const _DecisionSubjourneyNavigation({
    required this.showBack,
    required this.onBack,
    required this.onNext,
    required this.nextLabel,
  });

  final bool showBack;
  final VoidCallback onBack;
  final VoidCallback? onNext;
  final String nextLabel;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    return Row(
      children: [
        if (showBack) ...[
          Expanded(
            child: OutlinedButton.icon(
              key: const ValueKey('decision-subjourney-back'),
              onPressed: onBack,
              icon: const Icon(Icons.arrow_back_rounded),
              label: Text(strings.decisionJourneyBack),
            ),
          ),
          const SizedBox(width: 10),
        ],
        Expanded(
          flex: showBack ? 2 : 1,
          child: FilledButton.icon(
            key: const ValueKey('decision-subjourney-next'),
            onPressed: onNext,
            icon: const Icon(Icons.arrow_forward_rounded),
            label: Text(nextLabel),
          ),
        ),
      ],
    );
  }
}

class _DecisionReviewStage extends ConsumerWidget {
  const _DecisionReviewStage({
    required this.caseData,
    required this.responses,
    required this.selectedReasonTags,
    required this.reasonText,
    required this.onBack,
    required this.reviewAction,
  });

  final DecisionCase caseData;
  final Map<String, Object?> responses;
  final Set<String> selectedReasonTags;
  final String reasonText;
  final VoidCallback? onBack;
  final Widget reviewAction;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final content = ref.watch(kefeContentLocalizerProvider);
    return Column(
      key: const ValueKey('decision-subjourney-review'),
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        KefeSurface(
          tone: KefeSurfaceTone.raised,
          accent: visual.success,
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                strings.decisionJourneyReviewHelper,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: visual.mutedForeground,
                  height: 1.42,
                ),
              ),
              const SizedBox(height: 14),
              for (
                var index = 0;
                index < caseData.questions.length;
                index++
              ) ...[
                _ReviewAnswerRow(
                  prompt: content.text(
                    namespace: KefeContentNamespace.questionPrompt,
                    id: caseData.questions[index].id,
                    locale: strings.locale,
                    fallback: caseData.questions[index].prompt,
                  ),
                  answer: responses[caseData.questions[index].id],
                  optional: !caseData.questions[index].required,
                ),
                if (index != caseData.questions.length - 1)
                  const SizedBox(height: 10),
              ],
              if (caseData.reasonPolicy != null) ...[
                const SizedBox(height: 14),
                Divider(color: visual.border),
                const SizedBox(height: 10),
                Text(
                  selectedReasonTags.isEmpty && reasonText.trim().isEmpty
                      ? strings.decisionJourneyNoReason
                      : strings.decisionJourneyReasonSummary(
                          selectedReasonTags.length,
                          reasonText.trim().isNotEmpty,
                        ),
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: visual.mutedForeground,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ],
          ),
        ),
        if (onBack != null) ...[
          const SizedBox(height: 12),
          OutlinedButton.icon(
            key: const ValueKey('decision-subjourney-review-back'),
            onPressed: onBack,
            icon: const Icon(Icons.edit_outlined),
            label: Text(strings.decisionJourneyEdit),
          ),
        ],
        const SizedBox(height: 12),
        reviewAction,
      ],
    );
  }
}

class _ReviewAnswerRow extends StatelessWidget {
  const _ReviewAnswerRow({
    required this.prompt,
    required this.answer,
    required this.optional,
  });

  final String prompt;
  final Object? answer;
  final bool optional;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(
          answer == null ? Icons.remove_circle_outline : Icons.check_circle,
          color: answer == null ? visual.mutedForeground : visual.success,
          size: 20,
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                prompt,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(
                  context,
                ).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 3),
              Text(
                answer?.toString() ??
                    (optional
                        ? strings.decisionJourneySkipped
                        : strings.completeRequired),
                style: Theme.of(
                  context,
                ).textTheme.bodySmall?.copyWith(color: visual.mutedForeground),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
