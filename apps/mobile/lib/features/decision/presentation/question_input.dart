import 'package:flutter/material.dart';

import '../../../core/design/kefe_theme.dart';
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
    final isConfidence = question.responseType == 'CONFIDENCE';
    return Card(
      key: ValueKey('question-${question.id}'),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 38,
                  height: 38,
                  decoration: BoxDecoration(
                    color: (isConfidence
                            ? KefeColorTokens.gold
                            : KefeColorTokens.rules)
                        .withValues(alpha: 0.10),
                    borderRadius: BorderRadius.circular(11),
                  ),
                  child: Icon(
                    isConfidence
                        ? Icons.speed_rounded
                        : Icons.balance_outlined,
                    color: isConfidence
                        ? KefeColorTokens.goldSoft
                        : KefeColorTokens.rules,
                    size: 20,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        isConfidence ? 'EMİNLİK' : 'KARAR',
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                              color: isConfidence
                                  ? KefeColorTokens.goldSoft
                                  : KefeColorTokens.rules,
                              fontWeight: FontWeight.w900,
                              letterSpacing: 0.8,
                            ),
                      ),
                      const SizedBox(height: 5),
                      Text(
                        question.prompt,
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.w800,
                              height: 1.25,
                            ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 10),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Theme.of(context)
                        .colorScheme
                        .outlineVariant
                        .withValues(alpha: 0.24),
                    borderRadius: BorderRadius.circular(99),
                  ),
                  child: Text(
                    question.required
                        ? strings.requiredQuestion
                        : strings.optionalQuestion,
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: KefeColorTokens.textMutedDark,
                        ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 18),
            _QuestionInput(
              question: question,
              value: value,
              enabled: enabled,
              onChanged: onChanged,
            ),
          ],
        ),
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
    if (question.responseType == 'SINGLE_CHOICE' &&
        question.options.length == 2) {
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
                color: KefeColorTokens.rules,
                selected: effectiveIndex == 0,
                enabled: enabled,
                onTap: () => onChanged(question.options[0]),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: _BalanceOptionTile(
                option: question.options[1],
                color: KefeColorTokens.empathy,
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
    return Semantics(
      selected: selected,
      button: true,
      child: InkWell(
        key: ValueKey('option-$option'),
        onTap: enabled ? onTap : null,
        borderRadius: BorderRadius.circular(15),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          constraints: const BoxConstraints(minHeight: 82),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 13),
          decoration: BoxDecoration(
            color: selected
                ? color.withValues(alpha: 0.13)
                : KefeColorTokens.surfaceElevatedDark.withValues(alpha: 0.46),
            borderRadius: BorderRadius.circular(15),
            border: Border.all(
              color: selected
                  ? color.withValues(alpha: 0.72)
                  : Theme.of(context).colorScheme.outlineVariant,
              width: selected ? 1.6 : 1,
            ),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              AnimatedContainer(
                duration: const Duration(milliseconds: 180),
                width: 25,
                height: 25,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: selected ? color : Colors.transparent,
                  border: Border.all(
                    color: selected ? color : KefeColorTokens.textMutedDark,
                    width: 1.5,
                  ),
                ),
                child: selected
                    ? const Icon(
                        Icons.check_rounded,
                        size: 17,
                        color: Color(0xFF07111F),
                      )
                    : null,
              ),
              const SizedBox(height: 9),
              Text(
                option,
                textAlign: TextAlign.center,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: selected ? color : null,
                      fontWeight: selected ? FontWeight.w900 : FontWeight.w700,
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
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final option in question.options) ...[
          Semantics(
            selected: value == option,
            button: true,
            child: InkWell(
              key: ValueKey('option-$option'),
              onTap: enabled ? () => onChanged(option) : null,
              borderRadius: BorderRadius.circular(14),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 160),
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
                decoration: BoxDecoration(
                  color: value == option
                      ? KefeColorTokens.gold.withValues(alpha: 0.10)
                      : KefeColorTokens.surfaceElevatedDark.withValues(alpha: 0.48),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(
                    color: value == option
                        ? KefeColorTokens.gold.withValues(alpha: 0.58)
                        : Theme.of(context).colorScheme.outlineVariant,
                  ),
                ),
                child: Row(
                  children: [
                    AnimatedContainer(
                      duration: const Duration(milliseconds: 160),
                      width: 22,
                      height: 22,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: value == option
                            ? KefeColorTokens.gold
                            : Colors.transparent,
                        border: Border.all(
                          color: value == option
                              ? KefeColorTokens.gold
                              : KefeColorTokens.textMutedDark,
                          width: 1.6,
                        ),
                      ),
                      child: value == option
                          ? const Icon(
                              Icons.check_rounded,
                              size: 15,
                              color: Color(0xFF171106),
                            )
                          : null,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        option,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              fontWeight: value == option
                                  ? FontWeight.w800
                                  : FontWeight.w600,
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
    final values = _values();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Text(
              _label(question.minimum),
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: KefeColorTokens.textMutedDark,
                  ),
            ),
            const Spacer(),
            if (value != null)
              Text(
                '${_label((value as num).toDouble())}/10',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: KefeColorTokens.goldSoft,
                      fontWeight: FontWeight.w900,
                    ),
              ),
            const Spacer(),
            Text(
              _label(question.maximum),
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: KefeColorTokens.textMutedDark,
                  ),
            ),
          ],
        ),
        const SizedBox(height: 9),
        Wrap(
          spacing: 6,
          runSpacing: 8,
          alignment: WrapAlignment.center,
          children: [
            for (final item in values)
              Semantics(
                selected: _sameValue(value, item),
                button: true,
                child: ChoiceChip(
                  key: ValueKey(
                    'confidence-${question.id}-${_label(item)}',
                  ),
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
    for (var current = question.minimum;
        current <= question.maximum + 1e-9;
        current += step) {
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
