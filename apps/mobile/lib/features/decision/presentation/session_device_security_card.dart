import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/session_device_security_models.dart';

class SessionDeviceSecurityCard extends StatelessWidget {
  const SessionDeviceSecurityCard({
    required this.device,
    this.onRevoke,
    this.onTap,
    super.key,
  });

  final SessionDeviceModel device;
  final VoidCallback? onRevoke;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _tierColor(visual, device.trustTier);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('session-device-${device.sessionId}'),
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
                child: Icon(Icons.devices_rounded, color: accent, size: 22),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    KefeEyebrow(strings.sessDevEyebrow, color: accent),
                    const SizedBox(height: 2),
                    Text(
                      _tierLabel(strings, device.trustTier),
                      style: TextStyle(
                        fontSize: 12.5,
                        fontWeight: FontWeight.w800,
                        color: visual.foreground,
                      ),
                    ),
                  ],
                ),
              ),
              if (device.isCurrentDevice)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
                  decoration: BoxDecoration(
                    color: visual.surfaceSunken,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                  ),
                  child: Text(
                    strings.sessDevCurrentDeviceLabel,
                    style: TextStyle(
                      fontSize: 9,
                      fontWeight: FontWeight.w800,
                      color: visual.gold,
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            device.deviceName,
            style: TextStyle(
              fontSize: 12.5,
              fontWeight: FontWeight.w800,
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
            child: Text(
              strings.sessDevMetaLabel(device.clientPlatform.name, device.ipCountryCode),
              style: TextStyle(
                fontSize: 11.5,
                fontWeight: FontWeight.w700,
                color: visual.foreground,
              ),
            ),
          ),
        ],
      ),
    ),);
  }

  Color _tierColor(KefeVisualSystem visual, DeviceTrustTierModel tier) => switch (tier) {
    DeviceTrustTierModel.hardwareAttestedSecure => visual.rules,
    DeviceTrustTierModel.standardAuthenticated => visual.gold,
    DeviceTrustTierModel.unrecognizedStale => visual.empathy,
  };

  String _tierLabel(KefeStrings strings, DeviceTrustTierModel tier) => switch (tier) {
    DeviceTrustTierModel.hardwareAttestedSecure => strings.sessDevTierHardware,
    DeviceTrustTierModel.standardAuthenticated => strings.sessDevTierStandard,
    DeviceTrustTierModel.unrecognizedStale => strings.sessDevTierStale,
  };
}
