import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/change_mind_inquiry_models.dart';

class ChangeMindInquiryCard extends StatelessWidget {
  const ChangeMindInquiryCard({
    required this.inquiry,
    this.onTap,
    super.key,
  });

  final ChangeMindInquiryModel inquiry;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _classColor(visual, inquiry.flexibilityClass);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('change-mind-${inquiry.caseVersionId}'),
        tone: KefeSurfaceTone.raised,
        padding: const EdgeInsets.all(18),
        borderRadius: 22,
        accent: accent,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: accent.withValues(alpha: visual.isDark ? 0.18 : 0.10),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: accent.withValues(alpha: 0.3)),
                  ),
                  child: Icon(Icons.psychology_alt_outlined, color: accent, size: 20),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.changeMindEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _classLabel(strings, inquiry.flexibilityClass),
                        style: TextStyle(
                          fontSize: 12.5,
                          fontWeight: FontWeight.w800,
                          color: visual.foreground,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              strings.changeMindQuestion,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w700,
                color: visual.foreground,
              ),
            ),
            const SizedBox(height: 10),
            Column(
              children: inquiry.selectedConditions.map((cond) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: visual.surfaceSunken,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(_conditionIcon(cond.conditionType), size: 14, color: accent),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            cond.description,
                            style: TextStyle(
                              fontSize: 11.5,
                              fontWeight: FontWeight.w600,
                              color: visual.foreground,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  Color _classColor(KefeVisualTheme visual, EpistemicFlexibilityClassModel flexClass) =>
      switch (flexClass) {
        EpistemicFlexibilityClassModel.highlyEpistemicOpen => visual.rules,
        EpistemicFlexibilityClassModel.conditionallyFlexible => visual.gold,
        EpistemicFlexibilityClassModel.categoricalAbsolute => visual.empathy,
      };

  String _classLabel(KefeStrings strings, EpistemicFlexibilityClassModel flexClass) =>
      switch (flexClass) {
        EpistemicFlexibilityClassModel.highlyEpistemicOpen => strings.changeMindClassOpen,
        EpistemicFlexibilityClassModel.conditionallyFlexible =>
            strings.changeMindClassConditional,
        EpistemicFlexibilityClassModel.categoricalAbsolute =>
            strings.changeMindClassAbsolute,
      };

  IconData _conditionIcon(CounterfactualConditionTypeModel type) => switch (type) {
    CounterfactualConditionTypeModel.empiricalDataThreshold => Icons.analytics_outlined,
    CounterfactualConditionTypeModel.vulnerabilityProtection => Icons.shield_outlined,
    CounterfactualConditionTypeModel.economicSustainability =>
        Icons.account_balance_wallet_outlined,
    CounterfactualConditionTypeModel.moralImpasseEmpathy => Icons.favorite_border_rounded,
    CounterfactualConditionTypeModel.unconditionalStance => Icons.lock_outline_rounded,
  };
}
