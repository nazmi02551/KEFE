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
class MyKefeDomainActivity {
  const MyKefeDomainActivity({
    required this.primaryDomain,
    required this.committedWeighCount,
    required this.lastCommittedAt,
  });

  final String primaryDomain;
  final int committedWeighCount;
  final DateTime? lastCommittedAt;
}

@immutable
class MyKefeRecentJourney {
  const MyKefeRecentJourney({
    required this.caseId,
    required this.caseVersionId,
    required this.title,
    required this.primaryDomain,
    required this.initialCommittedAt,
    required this.latestDecisionAt,
    required this.decisionUpdateCount,
    required this.reflectionCompleted,
  });

  final String caseId;
  final String caseVersionId;
  final String title;
  final String primaryDomain;
  final DateTime initialCommittedAt;
  final DateTime latestDecisionAt;
  final int decisionUpdateCount;
  final bool reflectionCompleted;
}

@immutable
class MyKefeJourney {
  const MyKefeJourney({
    required this.decisionUpdateCount,
    required this.revisitedCaseCount,
    required this.reflectionCompletionCount,
    required this.domainActivity,
    required this.recentJourneys,
  });

  const MyKefeJourney.empty()
      : decisionUpdateCount = 0,
        revisitedCaseCount = 0,
        reflectionCompletionCount = 0,
        domainActivity = const [],
        recentJourneys = const [];

  final int decisionUpdateCount;
  final int revisitedCaseCount;
  final int reflectionCompletionCount;
  final List<MyKefeDomainActivity> domainActivity;
  final List<MyKefeRecentJourney> recentJourneys;

  bool get hasEnrichment =>
      decisionUpdateCount > 0 ||
      revisitedCaseCount > 0 ||
      reflectionCompletionCount > 0 ||
      domainActivity.isNotEmpty ||
      recentJourneys.isNotEmpty;
}

@immutable
class ProgressEnvelope {
  const ProgressEnvelope({
    required this.accountOffer,
    required this.progress,
    required this.methodology,
    this.journey = const MyKefeJourney.empty(),
  });

  final AccountOffer accountOffer;
  final MyKefeProgress progress;
  final MyKefeJourney journey;
  final Map<String, String> methodology;
}
