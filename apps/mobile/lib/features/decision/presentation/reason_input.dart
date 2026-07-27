import 'package:flutter/material.dart';

import '../../../core/localization/kefe_strings.dart';
import '../domain/decision_models.dart';

class ReasonInputCard extends StatelessWidget {
  const ReasonInputCard({
    required this.policy,
    required this.selectedTags,
    required this.text,
    required this.enabled,
    required this.onTagToggled,
    required this.onTextChanged,
    super.key,
  });

  final ReasonPolicy policy;
  final Set<String> selectedTags;
  final String text;
  final bool enabled;
  final ValueChanged<String> onTagToggled;
  final ValueChanged<String> onTextChanged;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    return Card(
      key: const ValueKey('reason-card'),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(strings.reasonTitle, style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            Text(strings.reasonHelper),
            if (policy.tags.isNotEmpty) ...[
              const SizedBox(height: 16),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final tag in policy.tags)
                    FilterChip(
                      key: ValueKey('reason-tag-$tag'),
                      label: Text(strings.reasonTagLabel(tag)),
                      selected: selectedTags.contains(tag),
                      onSelected: enabled ? (_) => onTagToggled(tag) : null,
                    ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                strings.reasonSelectionLimit(policy.maxTags),
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
            if (policy.textEnabled) ...[
              const SizedBox(height: 16),
              TextFormField(
                key: const ValueKey('reason-text'),
                initialValue: text,
                enabled: enabled,
                maxLength: policy.textMaxLength,
                minLines: 2,
                maxLines: 4,
                decoration: InputDecoration(
                  labelText: strings.reasonTextLabel,
                  hintText: strings.reasonTextHint,
                  border: const OutlineInputBorder(),
                ),
                onChanged: onTextChanged,
              ),
            ],
          ],
        ),
      ),
    );
  }
}
