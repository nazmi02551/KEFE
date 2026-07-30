import 'package:flutter/material.dart';

import '../../../core/design/kefe_theme.dart';
import '../../../core/localization/internal_alpha_strings.dart';
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
                    color: const Color(0xFF8E7CFF).withValues(alpha: 0.10),
                    borderRadius: BorderRadius.circular(11),
                  ),
                  child: const Icon(
                    Icons.format_quote_rounded,
                    color: Color(0xFFAA9CFF),
                    size: 21,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        strings.reasonsEyebrow,
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: const Color(0xFFAA9CFF),
                          fontWeight: FontWeight.w900,
                          letterSpacing: 0.8,
                        ),
                      ),
                      const SizedBox(height: 5),
                      Text(
                        strings.reasonTitle,
                        style: Theme.of(context).textTheme.titleMedium
                            ?.copyWith(fontWeight: FontWeight.w800),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              strings.reasonHelper,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: KefeColorTokens.textMutedDark,
                height: 1.4,
              ),
            ),
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
                      checkmarkColor: const Color(0xFF171106),
                      selectedColor: KefeColorTokens.gold,
                      labelStyle: TextStyle(
                        color: selectedTags.contains(tag)
                            ? const Color(0xFF171106)
                            : Theme.of(context).colorScheme.onSurface,
                        fontWeight: FontWeight.w700,
                      ),
                      onSelected: enabled ? (_) => onTagToggled(tag) : null,
                    ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                strings.reasonSelectionLimit(policy.maxTags),
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: KefeColorTokens.textMutedDark,
                ),
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
                  filled: true,
                  fillColor: KefeColorTokens.surfaceElevatedDark.withValues(
                    alpha: 0.55,
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(14),
                    borderSide: const BorderSide(
                      color: KefeColorTokens.borderDark,
                    ),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(14),
                    borderSide: const BorderSide(color: KefeColorTokens.gold),
                  ),
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
