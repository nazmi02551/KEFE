import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/decision_models.dart';
import 'kefe_balance_visual.dart';

class QuestionInputCard extends StatelessWidget {
  const QuestionInputCard({
    required this.question,
    required this.value,
    required this.enabled,
    required this.onChanged,
    super.key,
  });

  final DecisionQuestion question;
  final Object? value;
  final bool enabled;
  final ValueChanged<Object> onChanged;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final isConfidence = question.responseType == 'CONFIDENCE';
    final accent = isConfidence ? visual.gold : visual.rules;

    return KefeSurface(
      key: ValueKey('question-${question.id}'),
      tone: KefeSurfaceTone.raised,
      padding: const EdgeInsets.all(19),
      accent: accent,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: accent.withValues(alpha: visual.isDark ? 0.14 : 0.09),
                  borderRadius: BorderRadius.circular(13),
                  border: Border.all(color: accent.withValues(alpha: 0.18)),
                ),
                child: Icon(
                  isConfidence ? Icons.speed_rounded : Icons.balance_outlined,
                  color: accent,
                  size: 21,
                ),
              ),
              const SizedBox(width: 13),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    KefeEyebrow(
                      isConfidence
                          ? strings.questionConfidence
                          : strings.questionDecision,
                      color: accent,
                    ),
                    const SizedBox(height: 7),
                    Text(
                      question.prompt,
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w900,
                        height: 1.20,
                        letterSpacing: -0.25,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 10),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
                decoration: BoxDecoration(
                  color: visual.surfaceSunken,
                  borderRadius: BorderRadius.circular(99),
                  border: Border.all(color: visual.border.withValues(alpha: 0.78)),
                ),
                child: Text(
                  question.required
                      ? strings.requiredQuestion
                      : strings.optionalQuestion,
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: visual.mutedForeground,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          _QuestionInput(
            question: question,
            value: value,
            enabled: enabled,
            onChanged: onChanged,
          ),
        ],
      ),
    );
  }
}

class _QuestionInput extends StatelessWidget {
  const _QuestionInput({
    required this.question,
    required this.value,
    required this.enabled,
    required this.onChanged,
  });

  final DecisionQuestion question;
  final Object? value;
  final bool enabled;
  final ValueChanged<Object> onChanged;

  @override
  Widget build(BuildContext context) {
    if (question.responseType == 'SINGLE_CHOICE' && question.options.length == 2) {
      return _BalanceChoiceInput(
        question: question,
        value: value,
        enabled: enabled,
        onChanged: onChanged,
      );
    }

    return switch (question.responseType) {
      'SINGLE_CHOICE' => _SingleChoiceInput(
        question: question,
        value: value,
        enabled: enabled,
        onChanged: onChanged,
      ),
      'CONFIDENCE' => _ConfidenceInput(
        question: question,
        value: value,
        enabled: enabled,
        onChanged: onChanged,
      ),
      _ => _UnsupportedQuestion(responseType: question.responseType),
    };
  }
}

class _BalanceChoiceInput extends StatelessWidget {
  const _BalanceChoiceInput({
    required this.question,
    required this.value,
    required this.enabled,
    required this.onChanged,
  });

  final DecisionQuestion question;
  final Object? value;
  final bool enabled;
  final ValueChanged<Object> onChanged;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final selectedIndex = question.options.indexWhere((option) => option == value);
    final effectiveIndex = selectedIndex < 0 ? null : selectedIndex;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        KefeBalanceVisual(
          leftLabel: question.options[0],
          rightLabel: question.options[1],
          selectedIndex: effectiveIndex,
        ),
        const SizedBox(height: 14),
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: _BalanceOptionTile(
                option: question.options[0],
                color: visual.rules,
                selected: effectiveIndex == 0,
                enabled: enabled,
                onTap: () => onChanged(question.options[0]),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: _BalanceOptionTile(
                option: question.options[1],
                color: visual.empathy,
                selected: effectiveIndex == 1,
                enabled: enabled,
                onTap: () => onChanged(question.options[1]),
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _BalanceOptionTile extends StatelessWidget {
  const _BalanceOptionTile({
    required this.option,
    required this.color,
    required this.selected,
    required this.enabled,
    required this.onTap,
  });

  final String option;
  final Color color;
  final bool selected;
  final bool enabled;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final duration = KefeMotion.resolve(context, const Duration(milliseconds: 220));
    return Semantics(
      selected: selected,
      button: true,
      enabled: enabled,
      child: InkWell(
        key: ValueKey('option-$option'),
        onTap: enabled ? onTap : null,
        borderRadius: BorderRadius.circular(17),
        child: AnimatedContainer(
          duration: duration,
          curve: Curves.easeOutCubic,
          constraints: const BoxConstraints(minHeight: 90),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
          decoration: BoxDecoration(
            color: selected
                ? color.withValues(alpha: visual.isDark ? 0.18 : 0.10)
                : visual.surfaceSunken,
            borderRadius: BorderRadius.circular(17),
            border: Border.all(
              color: selected ? color.withValues(alpha: 0.82) : visual.border,
              width: selected ? 1.7 : 1,
            ),
            boxShadow: selected
                ? [
                    BoxShadow(
                      color: color.withValues(alpha: 0.11),
                      blurRadius: 18,
                      spreadRadius: 1,
                    ),
                  ]
                : const [],
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              AnimatedContainer(
                duration: duration,
                width: 27,
                height: 27,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: selected ? color : Colors.transparent,
                  border: Border.all(
                    color: selected ? color : visual.mutedForeground,
                    width: 1.5,
                  ),
                ),
                child: selected
                    ? Icon(
                        Icons.check_rounded,
                        size: 18,
                        color: visual.isDark ? const Color(0xFF07111F) : Colors.white,
                      )
                    : null,
              ),
              const SizedBox(height: 10),
              Text(
                option,
                textAlign: TextAlign.center,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: selected ? color : visual.foreground,
                  fontWeight: selected ? FontWeight.w900 : FontWeight.w750,
                  height: 1.22,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SingleChoiceInput extends StatelessWidget {
  const _SingleChoiceInput({
    required this.question,
    required this.value,
    required this.enabled,
    required this.onChanged,
  });

  final DecisionQuestion question;
  final Object? value;
  final bool enabled;
  final ValueChanged<Object> onChanged;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final duration = KefeMotion.resolve(context, const Duration(milliseconds: 200));
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final option in question.options) ...[
          Semantics(
            selected: value == option,
            button: true,
            enabled: enabled,
            child: InkWell(
              key: ValueKey('option-$option'),
              onTap: enabled ? () => onChanged(option) : null,
              borderRadius: BorderRadius.circular(15),
              child: AnimatedContainer(
                duration: duration,
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
                decoration: BoxDecoration(
                  color: value == option ? visual.subtleGoldSurface : visual.surfaceSunken,
                  borderRadius: BorderRadius.circular(15),
                  border: Border.all(
                    color: value == option
                        ? visual.gold.withValues(alpha: 0.62)
                        : visual.border,
                  ),
                ),
                child: Row(
                  children: [
                    AnimatedContainer(
                      duration: duration,
                      width: 23,
                      height: 23,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: value == option ? visual.gold : Colors.transparent,
                        border: Border.all(
                          color: value == option ? visual.gold : visual.mutedForeground,
                          width: 1.6,
                        ),
                      ),
                      child: value == option
                          ? const Icon(
                              Icons.check_rounded,
                              size: 16,
                              color: Color(0xFF171106),
                            )
                          : null,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        option,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          fontWeight: value == option ? FontWeight.w800 : FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(height: 10),
        ],
      ],
    );
  }
}

class _ConfidenceInput extends StatelessWidget {
  const _ConfidenceInput({
    required this.question,
    required this.value,
    required this.enabled,
    required this.onChanged,
  });

  final DecisionQuestion question;
  final Object? value;
  final bool enabled;
  final ValueChanged<Object> onChanged;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final values = _values();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Text(
              _label(question.minimum),
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: visual.mutedForeground,
                fontWeight: FontWeight.w700,
              ),
            ),
            const Spacer(),
            AnimatedSwitcher(
              duration: KefeMotion.resolve(context, const Duration(milliseconds: 180)),
              child: value == null
                  ? const SizedBox.shrink()
                  : Container(
                      key: ValueKey('confidence-current-$value'),
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                      decoration: BoxDecoration(
                        color: visual.subtleGoldSurface,
                        borderRadius: BorderRadius.circular(99),
                      ),
                      child: Text(
                        '${_label((value as num).toDouble())}/10',
                        style: Theme.of(context).textTheme.titleSmall?.copyWith(
                          color: visual.goldSoft,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                    ),
            ),
            const Spacer(),
            Text(
              _label(question.maximum),
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: visual.mutedForeground,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 7,
          runSpacing: 9,
          alignment: WrapAlignment.center,
          children: [
            for (final item in values)
              Semantics(
                selected: _sameValue(value, item),
                button: true,
                enabled: enabled,
                child: ChoiceChip(
                  key: ValueKey('confidence-${question.id}-${_label(item)}'),
                  label: Text(_label(item)),
                  selected: _sameValue(value, item),
                  onSelected: enabled ? (_) => onChanged(_normalized(item)) : null,
                ),
              ),
          ],
        ),
      ],
    );
  }

  bool _sameValue(Object? current, double item) =>
      current is num && current.toDouble() == item;

  List<double> _values() {
    final values = <double>[];
    final step = question.step <= 0 ? 1 : question.step;
    for (
      var current = question.minimum;
      current <= question.maximum + 1e-9;
      current += step
    ) {
      values.add(current);
      if (values.length >= 20) break;
    }
    return values;
  }

  Object _normalized(double value) =>
      value == value.roundToDouble() ? value.toInt() : value;

  String _label(double value) =>
      value == value.roundToDouble() ? '${value.toInt()}' : '$value';
}

class _UnsupportedQuestion extends StatelessWidget {
  const _UnsupportedQuestion({required this.responseType});

  final String responseType;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    return Semantics(
      liveRegion: true,
      child: Text('${strings.unsupportedQuestionType} ($responseType)'),
    );
  }
}
