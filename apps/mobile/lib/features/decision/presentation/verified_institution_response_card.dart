import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/verified_institution_response_models.dart';

class VerifiedInstitutionResponseCard extends StatelessWidget {
  const VerifiedInstitutionResponseCard({
    required this.response,
    this.onTap,
    super.key,
  });

  final VerifiedInstitutionResponseModel response;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = visual.rules;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('inst-response-${response.responseId}'),
        tone: KefeSurfaceTone.raised,
        padding: const EdgeInsets.all(18),
        borderRadius: 22,
        accent: accent,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: accent.withValues(alpha: visual.isDark ? 0.18 : 0.10),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: accent.withValues(alpha: 0.3)),
                  ),
                  child: Icon(Icons.assured_workload_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.instRespEyebrow, color: accent),
                      const SizedBox(height: 3),
                      Text(
                        response.institutionName,
                        style: TextStyle(
                          fontSize: 12.5,
                          fontWeight: FontWeight.w800,
                          color: visual.foreground,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
                        decoration: BoxDecoration(
                          color: accent.withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(color: accent.withValues(alpha: 0.4)),
                        ),
                        child: Text(
                          strings.instRespVerifiedBadge,
                          style: TextStyle(
                            fontSize: 9.5,
                            fontWeight: FontWeight.w900,
                            color: accent,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              _typeLabel(strings, response.institutionType),
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w700,
                color: visual.gold,
              ),
            ),
            const SizedBox(height: 6),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: visual.surfaceSunken,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: visual.border.withValues(alpha: 0.5)),
              ),
              child: Text(
                response.responseBody,
                style: TextStyle(
                  fontSize: 12,
                  color: visual.foreground,
                ),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              '${strings.instRespFingerprintLabel} ${response.verificationFingerprint.substring(0, 16)}...',
              style: TextStyle(
                fontSize: 10,
                fontFamily: 'monospace',
                color: visual.mutedForeground,
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _typeLabel(KefeStrings strings, InstitutionTypeModel type) => switch (type) {
    InstitutionTypeModel.officialGovernment => strings.instRespTypeGov,
    InstitutionTypeModel.municipalLocal => strings.instRespTypeMunicipal,
    InstitutionTypeModel.corporateEnterprise => strings.instRespTypeCorp,
    InstitutionTypeModel.civilSociety => strings.instRespTypeCivil,
  };
}
