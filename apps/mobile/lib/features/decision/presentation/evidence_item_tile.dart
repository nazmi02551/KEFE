import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/evidence_builder_models.dart';

class EvidenceItemTile extends StatelessWidget {
  const EvidenceItemTile({
    required this.evidence,
    this.onTap,
    super.key,
  });

  final StructuredEvidenceItemModel evidence;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final statusColor = _statusColor(visual, evidence.verificationStatus);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: KefeSurface(
        key: ValueKey('evidence-item-${evidence.evidenceId}'),
        tone: KefeSurfaceTone.raised,
        padding: const EdgeInsets.all(14),
        borderRadius: 16,
        accent: statusColor,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(_categoryIcon(evidence.category), size: 16, color: visual.rules),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    _categoryLabel(strings, evidence.category),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: visual.rules,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: statusColor.withValues(alpha: visual.isDark ? 0.16 : 0.08),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: statusColor.withValues(alpha: 0.3)),
                  ),
                  child: Text(
                    _statusLabel(strings, evidence.verificationStatus),
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w800,
                      color: statusColor,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              evidence.title,
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                fontWeight: FontWeight.w800,
                letterSpacing: -0.1,
              ),
            ),
            const SizedBox(height: 4),
            Row(
              children: [
                Text(
                  evidence.publisher,
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    color: visual.mutedForeground,
                  ),
                ),
                if (evidence.doiOrDocRef != null) ...[
                  const SizedBox(width: 8),
                  Text(
                    '• ${evidence.doiOrDocRef}',
                    style: TextStyle(
                      fontSize: 10.5,
                      color: visual.mutedForeground.withValues(alpha: 0.8),
                    ),
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }

  IconData _categoryIcon(EvidenceCategoryModel category) => switch (category) {
    EvidenceCategoryModel.academicPeerReviewed => Icons.school_outlined,
    EvidenceCategoryModel.officialGovernmentStat => Icons.account_balance_outlined,
    EvidenceCategoryModel.investigativeJournalism => Icons.newspaper_outlined,
    EvidenceCategoryModel.institutionalReport => Icons.summarize_outlined,
  };

  String _categoryLabel(KefeStrings strings, EvidenceCategoryModel category) =>
      switch (category) {
        EvidenceCategoryModel.academicPeerReviewed => strings.evidenceCategoryAcademic,
        EvidenceCategoryModel.officialGovernmentStat => strings.evidenceCategoryGov,
        EvidenceCategoryModel.investigativeJournalism =>
            strings.evidenceCategoryJournalism,
        EvidenceCategoryModel.institutionalReport =>
            strings.evidenceCategoryInstitutional,
      };

  Color _statusColor(
    KefeVisualTheme visual,
    EvidenceVerificationStatusModel status,
  ) =>
      switch (status) {
        EvidenceVerificationStatusModel.expertAudited => visual.gold,
        EvidenceVerificationStatusModel.communityVerified => visual.rules,
        EvidenceVerificationStatusModel.unverified => visual.mutedForeground,
      };

  String _statusLabel(
    KefeStrings strings,
    EvidenceVerificationStatusModel status,
  ) =>
      switch (status) {
        EvidenceVerificationStatusModel.expertAudited => strings.evidenceStatusExpert,
        EvidenceVerificationStatusModel.communityVerified =>
            strings.evidenceStatusCommunity,
        EvidenceVerificationStatusModel.unverified =>
            strings.evidenceStatusUnverified,
      };
}
