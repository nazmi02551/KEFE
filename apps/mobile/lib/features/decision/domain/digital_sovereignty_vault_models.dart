import 'package:flutter/foundation.dart';

enum DigitalSovereigntyTierModel {
  sovereignResidencyEnforced,
  controlledEphemeralCompute,
  dataExfiltrationBreachAlert,
}

@immutable
class DigitalSovereigntyModel {
  const DigitalSovereigntyModel({
    required this.vaultId,
    required this.jurisdictionRegion,
    required this.sovereigntyTier,
    required this.localResidencyPct,
    required this.exfiltrationThreatScore,
  });

  final String vaultId;
  final String jurisdictionRegion;
  final DigitalSovereigntyTierModel sovereigntyTier;
  final double localResidencyPct;
  final double exfiltrationThreatScore;
}
