import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/institution_response_models.dart';

class InstitutionResponseCard extends StatelessWidget {
  const InstitutionResponseCard({
    required this.response,
    super.key,
  });

  final InstitutionResponseItem response;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final isVerified = response.verificationStatus == AuthorityVerificationStatus.verified;

    return KefeSurface(
      key: ValueKey('institution-response-${response.id}'),
      tone: KefeSurfaceTone.raised,
      padding: const EdgeInsets.all(18),
      borderRadius: 22,
      accent: visual.rules,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: visual.rules.withValues(alpha: visual.isDark ? 0.16 : 0.08),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: visual.rules.withValues(alpha: 0.22)),
                ),
                child: Icon(Icons.account_balance_outlined, color: visual.rules, size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        KefeEyebrow(strings.institutionEyebrow, color: visual.rules),
                        if (isVerified) ...[
                          const SizedBox(width: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: visual.success.withValues(alpha: visual.isDark ? 0.18 : 0.10),
                              borderRadius: BorderRadius.circular(6),
                              border: Border.all(color: visual.success.withValues(alpha: 0.3)),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(Icons.verified_rounded, size: 11, color: visual.success),
                                const SizedBox(width: 3),
                                Text(
                                  strings.institutionVerifiedBadge,
                                  style: TextStyle(
                                    fontSize: 9.5,
                                    fontWeight: FontWeight.w800,
                                    color: visual.success,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      response.institutionName,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w900,
                        letterSpacing: -0.2,
                      ),
                    ),
                    Text(
                      response.authorityRole,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: visual.mutedForeground,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: visual.surfaceSunken,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: visual.border.withValues(alpha: 0.5)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.flag_outlined, size: 14, color: visual.goldSoft),
                const SizedBox(width: 6),
                Text(
                  _typeLabel(strings, response.responseType),
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                    color: visual.goldSoft,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          Text(
            response.statement,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              height: 1.45,
              color: visual.foreground,
            ),
          ),
          if (response.milestoneDate != null) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              decoration: BoxDecoration(
                color: visual.surfaceSunken.withValues(alpha: 0.5),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: visual.border.withValues(alpha: 0.4)),
              ),
              child: Row(
                children: [
                  Icon(Icons.event_outlined, size: 14, color: visual.mutedForeground),
                  const SizedBox(width: 6),
                  Text(
                    strings.institutionMilestoneLabel(
                      '${response.milestoneDate!.year}-${response.milestoneDate!.month.toString().padLeft(2, '0')}-${response.milestoneDate!.day.toString().padLeft(2, '0')}',
                    ),
                    style: TextStyle(fontSize: 11, color: visual.mutedForeground),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  String _typeLabel(KefeStrings strings, InstitutionResponseType type) => switch (type) {
    InstitutionResponseType.acknowledge => strings.institutionTypeAcknowledge,
    InstitutionResponseType.commitment => strings.institutionTypeCommitment,
    InstitutionResponseType.policyChange => strings.institutionTypePolicyChange,
    InstitutionResponseType.factualClarification => strings.institutionTypeClarification,
    InstitutionResponseType.declineWithReason => strings.institutionTypeDecline,
  };
}
