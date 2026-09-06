import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/institutional_promise_outcome_matrix_models.dart';

class InstitutionalPromiseOutcomeMatrixCard extends StatelessWidget {
  const InstitutionalPromiseOutcomeMatrixCard({
    required this.promise,
    this.onTap,
    super.key,
  });

  final PromiseOutcomeModel promise;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _statusColor(visual, promise.realizationStatus);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('prom-mtx-${promise.matrixId}'),
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
                  child: Icon(Icons.assignment_turned_in_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.promMtxEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _statusLabel(strings, promise.realizationStatus),
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
                    strings.promMtxCompletionLabel((promise.milestoneCompletionPct * 100).toInt()),
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
                '${promise.institutionName}: ${promise.promiseTitle}',
                style: TextStyle(
                  fontSize: 11.5,
                  color: visual.foreground,
                ),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              strings.promMtxProofsLabel(promise.empiricalEvidenceArtifactsCount),
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

  Color _statusColor(KefeVisualSystem visual, PromiseRealizationStatusModel status) => switch (status) {
    PromiseRealizationStatusModel.promiseDeliveredVerified => const Color(0xFF10B981),
    PromiseRealizationStatusModel.inProgressOnTrack => visual.gold,
    PromiseRealizationStatusModel.promiseBrokenDefault => visual.empathy,
  };

  String _statusLabel(KefeStrings strings, PromiseRealizationStatusModel status) => switch (status) {
    PromiseRealizationStatusModel.promiseDeliveredVerified => strings.promMtxStDelivered,
    PromiseRealizationStatusModel.inProgressOnTrack => strings.promMtxStProgress,
    PromiseRealizationStatusModel.promiseBrokenDefault => strings.promMtxStBroken,
  };
}
