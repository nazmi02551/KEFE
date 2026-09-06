import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/case_quality_checklist_models.dart';

class CaseQualityChecklistSheet extends StatelessWidget {
  const CaseQualityChecklistSheet({
    required this.checklist,
    super.key,
  });

  final CaseQualityChecklistModel checklist;

  static Future<void> show(
    BuildContext context,
    CaseQualityChecklistModel checklist,
  ) {
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => CaseQualityChecklistSheet(checklist: checklist),
    );
  }

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final isTr = strings.isTr;

    return Container(
      decoration: BoxDecoration(
        color: visual.surface,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
        border: Border.all(color: visual.border.withValues(alpha: 0.6)),
      ),
      padding: EdgeInsets.only(
        top: 20,
        left: 20,
        right: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: visual.borderStrong,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Icon(Icons.checklist_rtl_rounded, color: visual.rules, size: 24),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  strings.checklistSheetTitle,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w900,
                    letterSpacing: -0.2,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            strings.checklistMagicScoreRejected,
            style: TextStyle(
              fontSize: 12,
              color: visual.mutedForeground,
            ),
          ),
          const SizedBox(height: 14),
          _buildSummaryBanner(context, visual, strings),
          const SizedBox(height: 16),
          Flexible(
            child: SingleChildScrollView(
              child: Column(
                children: checklist.items.map((item) {
                  final statusColor = _statusColor(visual, item.status);
                  final name = isTr ? item.nameTr : item.nameEn;
                  final criterion = isTr ? item.criterionTr : item.criterionEn;

                  return Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: KefeSurface(
                      tone: KefeSurfaceTone.raised,
                      padding: const EdgeInsets.all(14),
                      borderRadius: 16,
                      accent: statusColor,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Expanded(
                                child: Text(
                                  name,
                                  style: TextStyle(
                                    fontSize: 13.5,
                                    fontWeight: FontWeight.w800,
                                    color: visual.foreground,
                                  ),
                                ),
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 8,
                                  vertical: 3,
                                ),
                                decoration: BoxDecoration(
                                  color: statusColor.withValues(
                                    alpha: visual.isDark ? 0.16 : 0.08,
                                  ),
                                  borderRadius: BorderRadius.circular(6),
                                  border: Border.all(
                                    color: statusColor.withValues(alpha: 0.35),
                                  ),
                                ),
                                child: Text(
                                  _statusLabel(strings, item.status),
                                  style: TextStyle(
                                    fontSize: 10.5,
                                    fontWeight: FontWeight.w900,
                                    color: statusColor,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          Text(
                            criterion,
                            style: TextStyle(
                              fontSize: 12,
                              color: visual.mutedForeground,
                              height: 1.35,
                            ),
                          ),
                          if (item.reviewerNote.isNotEmpty) ...[
                            const SizedBox(height: 8),
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Icon(
                                  Icons.verified_user_outlined,
                                  size: 14,
                                  color: statusColor,
                                ),
                                const SizedBox(width: 6),
                                Expanded(
                                  child: Text(
                                    item.reviewerNote,
                                    style: TextStyle(
                                      fontSize: 11.5,
                                      fontStyle: FontStyle.italic,
                                      color: visual.foreground.withValues(alpha: 0.85),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ],
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: visual.border.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                Icon(Icons.lock_clock_outlined, size: 13, color: visual.mutedForeground),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    '${strings.checklistMethodologyVerified}: ${checklist.methodologyHash}',
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
          const SizedBox(height: 12),
          OutlinedButton(
            onPressed: () => Navigator.of(context).pop(),
            child: Text(strings.checklistClose),
          ),
        ],
      ),
    );
  }

  Widget _buildSummaryBanner(
    BuildContext context,
    KefeVisualTheme visual,
    KefeStrings strings,
  ) {
    final isPass = checklist.isFullyAudited;
    final bannerColor = isPass ? visual.rules : visual.attention;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: bannerColor.withValues(alpha: visual.isDark ? 0.14 : 0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: bannerColor.withValues(alpha: 0.3)),
      ),
      child: Row(
        children: [
          Icon(
            isPass ? Icons.verified_rounded : Icons.pending_actions_rounded,
            color: bannerColor,
            size: 20,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  isPass
                      ? strings.checklistFullyAudited
                      : strings.checklistRevisionNeeded,
                  style: TextStyle(
                    fontSize: 12.5,
                    fontWeight: FontWeight.w800,
                    color: bannerColor,
                  ),
                ),
                Text(
                  '${checklist.verifiedCount}/${checklist.totalCount} boyutta tam doğrulama sağlandı',
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
  }

  Color _statusColor(KefeVisualTheme visual, QualityAuditStatusModel status) =>
      switch (status) {
        QualityAuditStatusModel.verified => visual.rules,
        QualityAuditStatusModel.pending => visual.gold,
        QualityAuditStatusModel.flagged => visual.attention,
      };

  String _statusLabel(KefeStrings strings, QualityAuditStatusModel status) =>
      switch (status) {
        QualityAuditStatusModel.verified => strings.checklistStatusVerified,
        QualityAuditStatusModel.pending => strings.checklistStatusPending,
        QualityAuditStatusModel.flagged => strings.checklistStatusFlagged,
      };
}
