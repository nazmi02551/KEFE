import 'package:flutter/foundation.dart';

enum IntergenerationalImpactStatusModel {
  regenerativeFutureStewardship,
  transitionalBurdenMonitored,
  intergenerationalDebtDepletion,
}

@immutable
class IntergenerationalJusticeModel {
  const IntergenerationalJusticeModel({
    required this.proxyId,
    required this.policyDomain,
    required this.impactStatus,
    required this.stewardshipEquityIndex,
    required this.planetaryBoundaryHeadroomScore,
  });

  final String proxyId;
  final String policyDomain;
  final IntergenerationalImpactStatusModel impactStatus;
  final double stewardshipEquityIndex;
  final double planetaryBoundaryHeadroomScore;
}
