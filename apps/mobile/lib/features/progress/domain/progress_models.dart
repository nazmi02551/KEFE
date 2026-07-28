import 'package:flutter/foundation.dart';

@immutable
class AccountOffer {
  const AccountOffer({
    required this.eligible,
    required this.placement,
    required this.blocking,
    required this.dismissible,
    required this.continueAsGuestAvailable,
    required this.accountCreationAvailable,
  });

  final bool eligible;
  final String placement;
  final bool blocking;
  final bool dismissible;
  final bool continueAsGuestAvailable;
  final bool accountCreationAvailable;
}

@immutable
class RecentProgressCase {
  const RecentProgressCase({
    required this.caseId,
    required this.caseVersionId,
    required this.title,
    required this.primaryDomain,
    required this.committedAt,
  });

  final String caseId;
  final String caseVersionId;
  final String title;
  final String primaryDomain;
  final DateTime committedAt;
}

@immutable
class MyKefeProgress {
  const MyKefeProgress({
    required this.readiness,
    required this.meaningfulWeighCount,
    required this.distinctCaseCount,
    required this.distinctDomainCount,
    required this.firstCommittedAt,
    required this.lastCommittedAt,
    required this.recentCases,
  });

  final String readiness;
  final int meaningfulWeighCount;
  final int distinctCaseCount;
  final int distinctDomainCount;
  final DateTime? firstCommittedAt;
  final DateTime? lastCommittedAt;
  final List<RecentProgressCase> recentCases;
}

@immutable
class ProgressEnvelope {
  const ProgressEnvelope({
    required this.accountOffer,
    required this.progress,
    required this.methodology,
  });

  final AccountOffer accountOffer;
  final MyKefeProgress progress;
  final Map<String, String> methodology;
}
