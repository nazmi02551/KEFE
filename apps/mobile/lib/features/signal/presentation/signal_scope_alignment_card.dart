import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/signal_scope_models.dart';

class SignalScopeAlignmentCard extends StatelessWidget {
  const SignalScopeAlignmentCard({
    required this.report,
    this.onTap,
    super.key,
  });

  final SignalScopeAlignmentReportModel report;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _statusColor(visual, report.alignmentStatus);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('signal-scope-alignment-${report.signalId}'),
        tone: KefeSurfaceTone.raised,
        padding: const EdgeInsets.all(18),
        borderRadius: 22,
        accent: accent,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header Row
            Row(
              children: [
                Container(
                  width: 38,
                  height: 38,
                  decoration: BoxDecoration(
                    color: accent.withValues(alpha: visual.isDark ? 0.18 : 0.10),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: accent.withValues(alpha: 0.3)),
                  ),
                  child: Icon(Icons.policy_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.sigScopeEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        strings.sigScopeTitle,
                        style: TextStyle(
                          fontSize: 14.5,
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

            // Status & Metrics Badges
            Wrap(
              spacing: 8,
              runSpacing: 6,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: accent.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: accent.withValues(alpha: 0.4)),
                  ),
                  child: Text(
                    _statusLabel(strings, report.alignmentStatus),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      color: accent,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: visual.surfaceSunken,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                  ),
                  child: Text(
                    strings.sigScopeScoreLabel((report.overallAlignmentScore * 100).round()),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: visual.foreground,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: visual.surfaceSunken,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                  ),
                  child: Text(
                    strings.sigScopeValidityLabel(report.validityWindowDays),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: visual.mutedForeground,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Scope Metadata Box
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: visual.surfaceSunken,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: visual.border.withValues(alpha: 0.4)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    strings.sigScopeJurisdictionLabel(report.jurisdictionLevel.toJsonValue()),
                    style: TextStyle(
                      fontSize: 11.5,
                      fontWeight: FontWeight.w700,
                      color: visual.foreground,
                    ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    strings.sigScopePopulationLabel(report.targetPopulation),
                    style: TextStyle(
                      fontSize: 11.5,
                      fontWeight: FontWeight.w600,
                      color: visual.mutedForeground,
                    ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    strings.sigScopeGeoLabel(report.geographicScope),
                    style: TextStyle(
                      fontSize: 11.5,
                      fontWeight: FontWeight.w600,
                      color: visual.mutedForeground,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 10),

            // Notice
            Text(
              strings.sigScopeNotice,
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w500,
                color: visual.mutedForeground,
                height: 1.35,
              ),
            ),
            const SizedBox(height: 12),

            // Dimensions Breakdown
            ...report.dimensions.map((dim) {
              final dimValidColor = dim.isValid ? visual.rules : visual.burgundy;
              return Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: visual.surfaceSunken.withValues(alpha: 0.7),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: visual.border.withValues(alpha: 0.3)),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Text(
                                dim.dimension,
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w800,
                                  color: visual.foreground,
                                ),
                              ),
                              const Spacer(),
                              Text(
                                '${(dim.alignmentScore * 100).round()}%',
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w700,
                                  color: dimValidColor,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 2),
                          Text(
                            '${dim.declaredScope} · ${dim.sampleScope}',
                            style: TextStyle(
                              fontSize: 10.5,
                              color: visual.mutedForeground,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: dimValidColor.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        dim.isValid ? strings.sigScopeDimensionValid : strings.sigScopeDimensionInvalid,
                        style: TextStyle(
                          fontSize: 9.5,
                          fontWeight: FontWeight.w800,
                          color: dimValidColor,
                        ),
                      ),
                    ),
                  ],
                ),
              );
            }),
            const SizedBox(height: 6),

            // Seal hash
            Text(
              strings.sigScopeSealVerified(
                report.scopeSealHash.length > 16
                    ? '${report.scopeSealHash.substring(0, 16)}...'
                    : report.scopeSealHash,
              ),
              style: TextStyle(
                fontSize: 9.5,
                fontFamily: 'monospace',
                color: visual.mutedForeground.withValues(alpha: 0.7),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _statusColor(KefeVisualSystem visual, ScopeAlignmentStatusModel status) {
    return switch (status) {
      ScopeAlignmentStatusModel.strictlyAligned => visual.rules,
      ScopeAlignmentStatusModel.overbroadWarning => visual.gold,
      ScopeAlignmentStatusModel.mismatchDisqualified => visual.burgundy,
    };
  }

  String _statusLabel(KefeStrings strings, ScopeAlignmentStatusModel status) {
    return switch (status) {
      ScopeAlignmentStatusModel.strictlyAligned => strings.sigScopeStAligned,
      ScopeAlignmentStatusModel.overbroadWarning => strings.sigScopeStOverbroad,
      ScopeAlignmentStatusModel.mismatchDisqualified => strings.sigScopeStDisqualified,
    };
  }
}

