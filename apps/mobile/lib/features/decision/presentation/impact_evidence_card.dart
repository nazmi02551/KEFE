import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/impact_evidence_models.dart';

class ImpactEvidenceCard extends StatelessWidget {
  const ImpactEvidenceCard({
    required this.evidence,
    this.onTap,
    super.key,
  });

  final ImpactEvidenceModel evidence;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _statusColor(visual, evidence.verificationStatus);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('impact-evidence-${evidence.evidenceId}'),
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
                  child: Icon(Icons.attachment_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.impactEviEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _typeLabel(strings, evidence.evidenceType),
                        style: TextStyle(
                          fontSize: 12.5,
                          fontWeight: FontWeight.w800,
                          color: visual.foreground,
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
                  decoration: BoxDecoration(
                    color: accent.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: accent.withValues(alpha: 0.4)),
                  ),
                  child: Text(
                    _statusBadge(strings, evidence.verificationStatus),
                    style: TextStyle(
                      fontSize: 9.5,
                      fontWeight: FontWeight.w900,
                      color: accent,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              evidence.evidenceTitle,
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w700,
                color: visual.foreground,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: visual.surfaceSunken,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: visual.border.withValues(alpha: 0.5)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '${strings.impactEviHashLabel} ${evidence.sha256Digest.substring(0, 20)}...',
                    style: TextStyle(
                      fontSize: 10,
                      fontFamily: 'monospace',
                      color: visual.mutedForeground,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    evidence.sourceUrl,
                    style: TextStyle(
                      fontSize: 10.5,
                      color: visual.rules,
                      decoration: TextDecoration.underline,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _statusColor(KefeVisualSystem visual, EvidenceVerificationStatusModel status) => switch (status) {
    EvidenceVerificationStatusModel.verifiedAuthentic => visual.rules,
    EvidenceVerificationStatusModel.pendingAudit => visual.gold,
    EvidenceVerificationStatusModel.challengedOrInsufficient => visual.empathy,
  };

  String _statusBadge(KefeStrings strings, EvidenceVerificationStatusModel status) => switch (status) {
    EvidenceVerificationStatusModel.verifiedAuthentic => strings.impactEviStatusVerified,
    EvidenceVerificationStatusModel.pendingAudit => strings.impactEviStatusPending,
    EvidenceVerificationStatusModel.challengedOrInsufficient => strings.impactEviStatusChallenged,
  };

  String _typeLabel(KefeStrings strings, ImpactEvidenceTypeModel type) => switch (type) {
    ImpactEvidenceTypeModel.officialGazetteDecree => strings.impactEviTypeGazette,
    ImpactEvidenceTypeModel.auditExpenditureReceipt => strings.impactEviTypeAudit,
    ImpactEvidenceTypeModel.sensorTelemetryData => strings.impactEviTypeSensor,
    ImpactEvidenceTypeModel.thirdPartyAcademicStudy => strings.impactEviTypeStudy,
  };
}
