import 'package:flutter/foundation.dart';

enum TradeoffProfileModel {
  healthEducationPriority,
  infrastructureGrowth,
  ecologicalTransition,
  balancedAllocation,
}

@immutable
class BudgetTradeoffModel {
  const BudgetTradeoffModel({
    required this.tradeoffId,
    required this.caseVersionId,
    required this.healthcarePct,
    required this.educationPct,
    required this.infrastructurePct,
    required this.greenTransitionPct,
    required this.unallocatedPct,
    required this.tradeoffProfile,
  });

  final String tradeoffId;
  final String caseVersionId;
  final int healthcarePct;
  final int educationPct;
  final int infrastructurePct;
  final int greenTransitionPct;
  final int unallocatedPct;
  final TradeoffProfileModel tradeoffProfile;
}
