import 'package:flutter/foundation.dart';

enum PrivacyBudgetStateModel {
  budgetHealthyAmple,
  budgetApproachingLimit,
  budgetExhaustedThrottled,
}

@immutable
class PrivacyBudgetModel {
  const PrivacyBudgetModel({
    required this.monitorId,
    required this.totalEpsilonBudget,
    required this.consumedEpsilon,
    required this.deltaParameter,
    required this.budgetState,
    required this.queriesExecutedCount,
  });

  final String monitorId;
  final double totalEpsilonBudget;
  final double consumedEpsilon;
  final double deltaParameter;
  final PrivacyBudgetStateModel budgetState;
  final int queriesExecutedCount;
}
