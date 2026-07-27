import 'package:flutter/material.dart';

import '../../../core/localization/kefe_strings.dart';
import '../domain/decision_models.dart';

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
    return Card(
      key: ValueKey('question-${question.id}'),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    question.prompt,
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                ),
                const SizedBox(width: 12),
                Text(
                  question.required ? strings.requiredQuestion : strings.optionalQuestion,
                  style: Theme.of(context).textTheme.labelSmall,
                ),
              ],
            ),
            const SizedBox(height: 16),
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
        for (final option in question.options)
          Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Semantics(
              selected: value == option,
              button: true,
              child: ChoiceChip(
                key: ValueKey('option-$option'),
                label: SizedBox(
                  width: double.infinity,
                  child: Text(option, textAlign: TextAlign.center),
                ),
                selected: value == option,
                onSelected: enabled ? (_) => onChanged(option) : null,
              ),
            ),
          ),
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
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        for (final item in values)
          Semantics(
            selected: value == item,
            button: true,
            child: ChoiceChip(
              key: ValueKey('confidence-${question.id}-${_label(item)}'),
              label: Text(_label(item)),
              selected: value == item,
              onSelected: enabled ? (_) => onChanged(_normalized(item)) : null,
            ),
          ),
      ],
    );
  }

  List<double> _values() {
    final values = <double>[];
    final step = question.step <= 0 ? 1 : question.step;
    for (var current = question.minimum; current <= question.maximum + 1e-9; current += step) {
      values.add(current);
      if (values.length >= 20) break;
    }
    return values;
  }

  Object _normalized(double value) => value == value.roundToDouble() ? value.toInt() : value;

  String _label(double value) => value == value.roundToDouble() ? '${value.toInt()}' : '$value';
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
