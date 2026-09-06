import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/segment_distribution_models.dart';

class SegmentDistributionCard extends StatelessWidget {
  const SegmentDistributionCard({
    required this.distribution,
    this.onTap,
    super.key,
  });

  final SegmentDistributionModel distribution;
  final VoidCallback? onTap;

  Color _cohortColor(KefeVisualSystem visual, String cohortType) => switch (cohortType) {
    'AGE_COHORT' => visual.rules,
    'URBAN_RURAL_COHORT' => visual.gold,
    'EXPERIENCE_LEVEL' => visual.empathy,
    'REGIONAL_COHORT' => visual.success,
    'STAKEHOLDER_ROLE' => visual.attention,
    _ => visual.mutedForeground,
  };

  String _cohortTypeLabel(KefeStrings strings, String cohortType) => switch (cohortType) {
    'AGE_COHORT' => strings.segmentDistTypeAge,
    'URBAN_RURAL_COHORT' => strings.segmentDistTypeUrbanRural,
    'EXPERIENCE_LEVEL' => strings.segmentDistTypeExperience,
    'REGIONAL_COHORT' => strings.segmentDistTypeRegional,
    'STAKEHOLDER_ROLE' => strings.segmentDistTypeStakeholder,
    _ => cohortType,
  };

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = visual.gold;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('segment-dist-${distribution.caseVersionId}'),
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
                  child: Icon(Icons.people_alt_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.segmentDistEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        strings.segmentDistTitle,
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                          color: visual.foreground,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 6,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: visual.success.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: visual.success.withValues(alpha: 0.28)),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.shield_rounded, size: 14, color: visual.success),
                      const SizedBox(width: 5),
                      Text(
                        strings.segmentDistPrivacyBadge(distribution.minimumSampleThreshold),
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: visual.success,
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: visual.mutedForeground.withValues(alpha: 0.08),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    strings.segmentDistOverallSample(distribution.overallSampleSize),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w500,
                      color: visual.mutedForeground,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            ...distribution.segments.map((seg) {
              final color = _cohortColor(visual, seg.cohortType);
              return Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: visual.isDark
                      ? Colors.white.withValues(alpha: 0.03)
                      : Colors.black.withValues(alpha: 0.02),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(
                    color: seg.isSuppressed
                        ? visual.mutedForeground.withValues(alpha: 0.15)
                        : color.withValues(alpha: 0.25),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Row(
                      children: [
                        Container(
                          width: 8,
                          height: 8,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: seg.isSuppressed ? visual.mutedForeground : color,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                _cohortTypeLabel(strings, seg.cohortType).toUpperCase(),
                                style: TextStyle(
                                  fontSize: 9,
                                  fontWeight: FontWeight.w700,
                                  letterSpacing: 0.6,
                                  color: color,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                seg.cohortLabel,
                                style: TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.w600,
                                  color: visual.foreground,
                                ),
                              ),
                            ],
                          ),
                        ),
                        Text(
                          'n=${seg.sampleSize}',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w500,
                            color: visual.mutedForeground,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    if (seg.isSuppressed) ...[
                      Row(
                        children: [
                          Icon(
                            Icons.lock_outline_rounded,
                            size: 14,
                            color: visual.mutedForeground,
                          ),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              strings.segmentDistSuppressedNotice(
                                distribution.minimumSampleThreshold,
                              ),
                              style: TextStyle(
                                fontSize: 11,
                                fontStyle: FontStyle.italic,
                                color: visual.mutedForeground,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ] else ...[
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          if (seg.primaryChoice != null)
                            Text(
                              strings.segmentDistPrimaryPref(seg.primaryChoice!),
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w600,
                                color: color,
                              ),
                            ),
                          Text(
                            strings.segmentDistEntropyLabel(
                              '${(seg.entropyScore * 100).toInt()}%',
                            ),
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w500,
                              color: visual.mutedForeground,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(4),
                        child: Row(
                          children: seg.optionShares.entries.map((entry) {
                            final share = entry.value;
                            final optColor = entry.key == 'A'
                                ? visual.rules
                                : visual.empathy;
                            return Expanded(
                              flex: (share * 1000).toInt(),
                              child: Container(
                                height: 8,
                                color: optColor.withValues(alpha: 0.85),
                              ),
                            );
                          }).toList(),
                        ),
                      ),
                    ],
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}
