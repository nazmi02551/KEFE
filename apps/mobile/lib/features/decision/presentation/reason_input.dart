import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
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
    final visual = context.kefeVisual;
    final accent = Color.lerp(
      visual.burgundy,
      visual.goldSoft,
      visual.isDark ? 0.48 : 0.20,
    )!;

    return KefeSurface(
      key: const ValueKey('reason-card'),
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
                  color: accent.withValues(alpha: visual.isDark ? 0.15 : 0.09),
                  borderRadius: BorderRadius.circular(13),
                  border: Border.all(color: accent.withValues(alpha: 0.18)),
                ),
                child: Icon(Icons.format_quote_rounded, color: accent, size: 22),
              ),
              const SizedBox(width: 13),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    KefeEyebrow(strings.reasonsEyebrow, color: accent),
                    const SizedBox(height: 7),
                    Text(
                      strings.reasonTitle,
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w900,
                        height: 1.20,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            strings.reasonHelper,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: visual.mutedForeground,
              height: 1.45,
            ),
          ),
          if (policy.tags.isNotEmpty) ...[
            const SizedBox(height: 17),
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
                    selectedColor: visual.gold,
                    backgroundColor: visual.surfaceSunken,
                    side: BorderSide(
                      color: selectedTags.contains(tag)
                          ? visual.gold.withValues(alpha: 0.72)
                          : visual.border,
                    ),
                    labelStyle: TextStyle(
                      color: selectedTags.contains(tag)
                          ? const Color(0xFF171106)
                          : visual.foreground,
                      fontWeight: FontWeight.w700,
                    ),
                    onSelected: enabled ? (_) => onTagToggled(tag) : null,
                  ),
              ],
            ),
            const SizedBox(height: 9),
            Text(
              strings.reasonSelectionLimit(policy.maxTags),
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: visual.mutedForeground,
              ),
            ),
          ],
          if (policy.textEnabled) ...[
            const SizedBox(height: 17),
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
                fillColor: visual.surfaceSunken,
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(15),
                  borderSide: BorderSide(color: visual.border),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(15),
                  borderSide: BorderSide(color: visual.gold, width: 1.5),
                ),
              ),
              onChanged: onTextChanged,
            ),
          ],
        ],
      ),
    );
  }
}
