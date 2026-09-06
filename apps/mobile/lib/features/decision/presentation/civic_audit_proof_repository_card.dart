import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/civic_audit_proof_repository_models.dart';

class CivicAuditProofRepositoryCard extends StatelessWidget {
  const CivicAuditProofRepositoryCard({
    required this.report,
    this.onTap,
    super.key,
  });

  final CivicAuditReportModel report;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _statusColor(visual, report.verificationStatus);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('civic-repo-${report.reportId}'),
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
                  child: Icon(Icons.verified_user_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.civicRepoEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _statusLabel(strings, report.verificationStatus),
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
                    color: visual.surfaceSunken,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                  ),
                  child: Text(
                    strings.civicRepoAttestationsLabel(report.peerAttestationSignaturesCount),
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w800,
                      color: accent,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: visual.surfaceSunken,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: visual.border.withValues(alpha: 0.5)),
              ),
              child: Text(
                report.investigationTitle,
                style: TextStyle(
                  fontSize: 11.5,
                  color: visual.foreground,
                ),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              strings.civicRepoRigorLabel((report.evidentiaryRigorScore * 100).toInt()),
              style: TextStyle(
                fontSize: 10.5,
                fontWeight: FontWeight.w700,
                color: visual.gold,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _statusColor(KefeVisualSystem visual, AuditVerificationStatusModel status) => switch (status) {
    AuditVerificationStatusModel.peerAttestedCorroborated => const Color(0xFF10B981),
    AuditVerificationStatusModel.openEvidentiaryChallenge => visual.gold,
    AuditVerificationStatusModel.pendingWitnessConfirmation => visual.empathy,
  };

  String _statusLabel(KefeStrings strings, AuditVerificationStatusModel status) => switch (status) {
    AuditVerificationStatusModel.peerAttestedCorroborated => strings.civicRepoStAttested,
    AuditVerificationStatusModel.openEvidentiaryChallenge => strings.civicRepoStChallenge,
    AuditVerificationStatusModel.pendingWitnessConfirmation => strings.civicRepoStPending,
  };
}
