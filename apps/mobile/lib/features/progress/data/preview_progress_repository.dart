import '../domain/progress_models.dart';
import 'progress_repository.dart';

class PreviewProgressRepository implements ProgressRepository {
  @override
  Future<ProgressEnvelope> fetchProgress() async {
    final activity = <MyKefeDomainActivity>[
      MyKefeDomainActivity(
        primaryDomain: 'DAILY_LIFE',
        committedWeighCount: 3,
        lastCommittedAt: DateTime.utc(2026, 7, 29, 18, 45),
      ),
      MyKefeDomainActivity(
        primaryDomain: 'TECHNOLOGY',
        committedWeighCount: 3,
        lastCommittedAt: DateTime.utc(2026, 7, 29, 16, 30),
      ),
      MyKefeDomainActivity(
        primaryDomain: 'WORK_ECONOMY',
        committedWeighCount: 2,
        lastCommittedAt: DateTime.utc(2026, 7, 28, 20, 10),
      ),
      MyKefeDomainActivity(
        primaryDomain: 'EDUCATION',
        committedWeighCount: 2,
        lastCommittedAt: DateTime.utc(2026, 7, 28, 17, 20),
      ),
      MyKefeDomainActivity(
        primaryDomain: 'SPORTS',
        committedWeighCount: 1,
        lastCommittedAt: DateTime.utc(2026, 7, 27, 19, 5),
      ),
      MyKefeDomainActivity(
        primaryDomain: 'CIVIC',
        committedWeighCount: 1,
        lastCommittedAt: DateTime.utc(2026, 7, 27, 14, 40),
      ),
    ];

    final recentJourneys = <MyKefeRecentJourney>[
      MyKefeRecentJourney(
        caseId: '11111111-1111-4111-8111-111111111116',
        caseVersionId: '22222222-2222-4222-8222-222222222227',
        title: 'Çocuklar uçakta ebeveynleriyle ücretsiz yan yana oturmalı mı?',
        primaryDomain: 'DAILY_LIFE',
        initialCommittedAt: DateTime.utc(2026, 7, 29, 18, 31),
        latestDecisionAt: DateTime.utc(2026, 7, 29, 18, 45),
        decisionUpdateCount: 1,
        reflectionCompleted: true,
      ),
      MyKefeRecentJourney(
        caseId: '11111111-1111-4111-8111-111111111112',
        caseVersionId: '22222222-2222-4222-8222-222222222223',
        title: 'Yapay zekâ şirketlerinin veri toplaması sınırlandırılmalı mı?',
        primaryDomain: 'TECHNOLOGY',
        initialCommittedAt: DateTime.utc(2026, 7, 29, 16, 30),
        latestDecisionAt: DateTime.utc(2026, 7, 29, 16, 30),
        decisionUpdateCount: 0,
        reflectionCompleted: false,
      ),
      MyKefeRecentJourney(
        caseId: '11111111-1111-4111-8111-111111111117',
        caseVersionId: '22222222-2222-4222-8222-222222222228',
        title:
            'YZ nedeniyle işten çıkarma öncesi yeniden eğitim zorunlu olmalı mı?',
        primaryDomain: 'WORK_ECONOMY',
        initialCommittedAt: DateTime.utc(2026, 7, 28, 19, 48),
        latestDecisionAt: DateTime.utc(2026, 7, 28, 20, 10),
        decisionUpdateCount: 1,
        reflectionCompleted: true,
      ),
      MyKefeRecentJourney(
        caseId: '11111111-1111-4111-8111-111111111118',
        caseVersionId: '22222222-2222-4222-8222-222222222229',
        title: 'Üniversitelerde üretken YZ kullanımı sınırlandırılmalı mı?',
        primaryDomain: 'EDUCATION',
        initialCommittedAt: DateTime.utc(2026, 7, 28, 17, 20),
        latestDecisionAt: DateTime.utc(2026, 7, 28, 17, 20),
        decisionUpdateCount: 0,
        reflectionCompleted: false,
      ),
      MyKefeRecentJourney(
        caseId: '11111111-1111-4111-8111-111111111113',
        caseVersionId: '22222222-2222-4222-8222-222222222224',
        title: 'Bu pozisyonda penaltı kararı doğru muydu?',
        primaryDomain: 'SPORTS',
        initialCommittedAt: DateTime.utc(2026, 7, 27, 19, 5),
        latestDecisionAt: DateTime.utc(2026, 7, 27, 19, 5),
        decisionUpdateCount: 0,
        reflectionCompleted: false,
      ),
    ];

    return ProgressEnvelope(
      accountOffer: const AccountOffer(
        eligible: false,
        placement: 'POST_REVEAL',
        blocking: false,
        dismissible: true,
        continueAsGuestAvailable: true,
        accountCreationAvailable: false,
      ),
      progress: MyKefeProgress(
        readiness: 'FORMING',
        meaningfulWeighCount: 12,
        distinctCaseCount: 8,
        distinctDomainCount: 6,
        firstCommittedAt: DateTime.utc(2026, 7, 20, 10),
        lastCommittedAt: DateTime.utc(2026, 7, 29, 18, 45),
        recentCases: recentJourneys
            .map(
              (item) => RecentProgressCase(
                caseId: item.caseId,
                caseVersionId: item.caseVersionId,
                title: item.title,
                primaryDomain: item.primaryDomain,
                committedAt: item.initialCommittedAt,
              ),
            )
            .toList(growable: false),
      ),
      journey: MyKefeJourney(
        decisionUpdateCount: 2,
        revisitedCaseCount: 2,
        reflectionCompletionCount: 2,
        domainActivity: activity,
        recentJourneys: recentJourneys,
      ),
      personalReport: MyKefePersonalReport(
        moments: [
          MyKefeReportMoment(
            type: MyKefeReportMomentType.reflectionCompleted,
            caseId: recentJourneys[0].caseId,
            caseVersionId: recentJourneys[0].caseVersionId,
            title: recentJourneys[0].title,
            primaryDomain: recentJourneys[0].primaryDomain,
            occurredAt: DateTime.utc(2026, 7, 29, 18, 52),
          ),
          MyKefeReportMoment(
            type: MyKefeReportMomentType.decisionUpdate,
            caseId: recentJourneys[0].caseId,
            caseVersionId: recentJourneys[0].caseVersionId,
            title: recentJourneys[0].title,
            primaryDomain: recentJourneys[0].primaryDomain,
            occurredAt: recentJourneys[0].latestDecisionAt,
            revisionNo: 2,
          ),
          MyKefeReportMoment(
            type: MyKefeReportMomentType.initialCommit,
            caseId: recentJourneys[0].caseId,
            caseVersionId: recentJourneys[0].caseVersionId,
            title: recentJourneys[0].title,
            primaryDomain: recentJourneys[0].primaryDomain,
            occurredAt: recentJourneys[0].initialCommittedAt,
          ),
          MyKefeReportMoment(
            type: MyKefeReportMomentType.initialCommit,
            caseId: recentJourneys[1].caseId,
            caseVersionId: recentJourneys[1].caseVersionId,
            title: recentJourneys[1].title,
            primaryDomain: recentJourneys[1].primaryDomain,
            occurredAt: recentJourneys[1].initialCommittedAt,
          ),
          MyKefeReportMoment(
            type: MyKefeReportMomentType.reflectionCompleted,
            caseId: recentJourneys[2].caseId,
            caseVersionId: recentJourneys[2].caseVersionId,
            title: recentJourneys[2].title,
            primaryDomain: recentJourneys[2].primaryDomain,
            occurredAt: DateTime.utc(2026, 7, 28, 20, 16),
          ),
          MyKefeReportMoment(
            type: MyKefeReportMomentType.decisionUpdate,
            caseId: recentJourneys[2].caseId,
            caseVersionId: recentJourneys[2].caseVersionId,
            title: recentJourneys[2].title,
            primaryDomain: recentJourneys[2].primaryDomain,
            occurredAt: recentJourneys[2].latestDecisionAt,
            revisionNo: 2,
          ),
          MyKefeReportMoment(
            type: MyKefeReportMomentType.initialCommit,
            caseId: recentJourneys[2].caseId,
            caseVersionId: recentJourneys[2].caseVersionId,
            title: recentJourneys[2].title,
            primaryDomain: recentJourneys[2].primaryDomain,
            occurredAt: recentJourneys[2].initialCommittedAt,
          ),
        ],
      ),
      methodology: const {
        'sample_scope': 'PRODUCT_PREVIEW_EXAMPLE_HISTORY',
        'readiness_note': 'PRESENTATION_ONLY_NOT_RESEARCH_VALIDATED',
        'advanced_insights': 'NONE',
        'data_mode': 'DETERMINISTIC_PREVIEW',
      },
    );
  }
}
