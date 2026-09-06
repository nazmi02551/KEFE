import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/signal_health_models.dart';

class SignalHealthCard extends StatelessWidget {
  const SignalHealthCard({
    required this.report,
    this.onTap,
    super.key,
  });

  final SignalHealthReportModel report;
  final VoidCallback? onTap;

  static Future<void> show(
    BuildContext context,
    SignalHealthReportModel report,
  ) {
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => Container(
        decoration: BoxDecoration(
          color: ctx.kefeVisual.surface,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
          border: Border.all(color: ctx.kefeVisual.border.withValues(alpha: 0.6)),
        ),
        padding: EdgeInsets.only(
          top: 20,
          left: 20,
          right: 20,
          bottom: MediaQuery.of(ctx).viewInsets.bottom + 24,
        ),
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: ctx.kefeVisual.borderStrong,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              SignalHealthCard(report: report),
              const SizedBox(height: 16),
              OutlinedButton(
                onPressed: () => Navigator.of(ctx).pop(),
                child: Text(KefeStrings.of(ctx).sigHealthClose),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final isTr = strings.isTr;
    final accent = _statusColor(visual, report.overallQualification);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('signal-health-${report.signalId}'),
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
                  child: Icon(Icons.health_and_safety_rounded, color: accent, size: 20),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.sigHealthEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _qualificationLabel(strings, report.overallQualification),
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w800,
                          color: visual.foreground,
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: accent.withValues(alpha: visual.isDark ? 0.20 : 0.10),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: accent.withValues(alpha: 0.4)),
                  ),
                  child: Text(
                    '%${report.overallHealthScore.toStringAsFixed(0)}',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w900,
                      color: accent,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              strings.sigHealthNotice,
              style: TextStyle(
                fontSize: 11.5,
                color: visual.mutedForeground,
                height: 1.35,
              ),
            ),
            const SizedBox(height: 14),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  strings.sigHealthScoreLabel(report.overallHealthScore),
                  style: TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w700,
                    color: visual.foreground,
                  ),
                ),
                Text(
                  strings.sigHealthSampleLabel(report.sampleSize),
                  style: TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w600,
                    color: visual.mutedForeground,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            const Divider(height: 1),
            const SizedBox(height: 12),
            ...report.dimensions.map((dim) {
              final dimPassed = dim.isPassed;
              final dimColor = dimPassed ? visual.rules : visual.attention;
              final dimTitle = isTr ? dim.titleTr : dim.titleEn;

              return Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(
                      dimPassed
                          ? Icons.check_circle_outline_rounded
                          : Icons.error_outline_rounded,
                      size: 16,
                      color: dimColor,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                dimTitle,
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w700,
                                  color: visual.foreground,
                                ),
                              ),
                              Text(
                                dimPassed
                                    ? strings.sigHealthPassed
                                    : strings.sigHealthFlagged,
                                style: TextStyle(
                                  fontSize: 10,
                                  fontWeight: FontWeight.w800,
                                  color: dimColor,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 2),
                          Text(
                            dim.detail,
                            style: TextStyle(
                              fontSize: 11,
                              color: visual.mutedForeground,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              );
            }),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
              decoration: BoxDecoration(
                color: visual.border.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(
                strings.sigHealthMethodologyVerified(report.methodologyHash),
                style: TextStyle(
                  fontSize: 10,
                  fontFamily: 'monospace',
                  color: visual.mutedForeground,
                ),
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _statusColor(
    KefeVisualTheme visual,
    SignalQualificationStatusModel status,
  ) =>
      switch (status) {
        SignalQualificationStatusModel.qualifiedSignal => visual.rules,
        SignalQualificationStatusModel.provisionalTrend => visual.gold,
        SignalQualificationStatusModel.unqualifiedNoise => visual.attention,
      };

  String _qualificationLabel(
    KefeStrings strings,
    SignalQualificationStatusModel status,
  ) =>
      switch (status) {
        SignalQualificationStatusModel.qualifiedSignal =>
          strings.sigHealthStQualified,
        SignalQualificationStatusModel.provisionalTrend =>
          strings.sigHealthStProvisional,
        SignalQualificationStatusModel.unqualifiedNoise =>
          strings.sigHealthStNoise,
      };
}
