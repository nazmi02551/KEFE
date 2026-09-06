import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/signal_versioning_models.dart';

class SignalVersioningCard extends StatelessWidget {
  const SignalVersioningCard({
    required this.report,
    this.onTap,
    super.key,
  });

  final SignalVersioningReportModel report;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = report.auditChainValid ? visual.rules : visual.burgundy;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('signal-versioning-${report.signalId}'),
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
                  child: Icon(Icons.alt_route_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.sigVersEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        strings.sigVersTitle,
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

            // Version & Audit Badges
            Wrap(
              spacing: 8,
              runSpacing: 6,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: visual.surfaceSunken,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                  ),
                  child: Text(
                    strings.sigVersCurrentVersionLabel(report.currentVersion),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      color: visual.foreground,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: accent.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: accent.withValues(alpha: 0.4)),
                  ),
                  child: Text(
                    report.auditChainValid ? strings.sigVersChainVerified : strings.sigVersChainInvalid,
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
                    '${report.snapshots.length} Snapshots',
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

            // Notice
            Text(
              strings.sigVersNotice,
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w500,
                color: visual.mutedForeground,
                height: 1.35,
              ),
            ),
            const SizedBox(height: 12),

            // Delta Box (if upgraded)
            if (report.latestDelta != null) ...[
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: visual.gold.withValues(alpha: visual.isDark ? 0.12 : 0.08),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: visual.gold.withValues(alpha: 0.35)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.change_circle_rounded, color: visual.gold, size: 16),
                        const SizedBox(width: 6),
                        Text(
                          strings.sigVersDeltaTitle,
                          style: TextStyle(
                            fontSize: 11.5,
                            fontWeight: FontWeight.w800,
                            color: visual.gold,
                          ),
                        ),
                        const Spacer(),
                        Text(
                          '${report.latestDelta!.fromVersion} -> ${report.latestDelta!.toVersion}',
                          style: TextStyle(
                            fontSize: 10.5,
                            fontWeight: FontWeight.w700,
                            fontFamily: 'monospace',
                            color: visual.foreground,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        Text(
                          strings.sigVersDeltaShiftLabel((report.latestDelta!.distributionShift * 100).round()),
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            color: visual.foreground,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Text(
                          strings.sigVersDeltaConfidenceLabel((report.latestDelta!.confidenceDelta * 100).round()),
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            color: visual.rules,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      report.latestDelta!.notes,
                      style: TextStyle(
                        fontSize: 10.5,
                        color: visual.mutedForeground,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
            ],

            // Snapshots List
            ...report.snapshots.map((snap) {
              final isCurrent = snap.methodologyVersion == report.currentVersion;
              return Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: visual.surfaceSunken.withValues(alpha: 0.7),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                    color: isCurrent ? visual.rules.withValues(alpha: 0.5) : visual.border.withValues(alpha: 0.3),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: isCurrent
                                ? visual.rules.withValues(alpha: 0.15)
                                : visual.mutedForeground.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            snap.methodologyVersion,
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.w800,
                              fontFamily: 'monospace',
                              color: isCurrent ? visual.rules : visual.foreground,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            snap.methodologyName,
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                              color: visual.foreground,
                            ),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      strings.sigVersSnapshotSample(snap.sampleSize, (snap.confidenceScore * 100).round()),
                      style: TextStyle(
                        fontSize: 10.5,
                        color: visual.mutedForeground,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      snap.parentSnapshotHash != null
                          ? strings.sigVersParentHash(
                              snap.parentSnapshotHash!.length > 12
                                  ? '${snap.parentSnapshotHash!.substring(0, 12)}...'
                                  : snap.parentSnapshotHash!,
                            )
                          : strings.sigVersGenesis,
                      style: TextStyle(
                        fontSize: 9.5,
                        fontFamily: 'monospace',
                        color: visual.mutedForeground.withValues(alpha: 0.6),
                      ),
                    ),
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
