import '../../../core/localization/kefe_locale_catalog.dart';
import '../../../core/localization/kefe_strings.dart';
import '../localization/progress_string_catalog.dart';

extension ProgressStrings on KefeStrings {
  String _progressText(
    String key, {
    Map<String, Object?> placeholders = const {},
  }) => KefeLocaleCatalog.resolve(
    locale: locale,
    resources: ProgressStringCatalog.resources,
    key: key,
    placeholders: placeholders,
  );

  String get progressTitle => _progressText('progress.title');
  String get progressLoading => _progressText('progress.loading');
  String get progressUnavailable => _progressText('progress.unavailable');
  String get progressRetry => _progressText('progress.retry');
  String get progressWeighs => _progressText('progress.weighs');
  String get progressCases => _progressText('progress.cases');
  String get progressDomains => _progressText('progress.domains');
  String get progressRecent => _progressText('progress.recent');
  String get progressMethodology => _progressText('progress.methodology');

  String progressReadiness(String readiness) =>
      _progressText(switch (readiness) {
        'FORMING' => 'progress.readiness.forming',
        _ => 'progress.readiness.default',
      });

  String get journeyEyebrow => _progressText('journey.eyebrow');
  String get journeyTitle => _progressText('journey.title');
  String get journeySubtitle => _progressText('journey.subtitle');
  String get journeyPreviewNotice => _progressText('journey.preview_notice');
  String get journeyRevisits => _progressText('journey.revisits');
  String get journeyReflections => _progressText('journey.reflections');
  String get journeyDomainActivity => _progressText('journey.domain_activity');
  String get journeyRecent => _progressText('journey.recent');
  String get journeyRevisited => _progressText('journey.revisited');
  String get journeyReflected => _progressText('journey.reflected');
  String get journeyCommitted => _progressText('journey.committed');
  String get journeyEmpty => _progressText('journey.empty');
  String get journeyNonInferenceNote =>
      _progressText('journey.non_inference_note');
  String get journeyNextEyebrow => _progressText('journey.next.eyebrow');
  String get journeyNextReflectionTitle =>
      _progressText('journey.next.reflection.title');
  String get journeyNextReflectionBody =>
      _progressText('journey.next.reflection.body');
  String get journeyNextRevisitTitle =>
      _progressText('journey.next.revisit.title');
  String get journeyNextRevisitBody =>
      _progressText('journey.next.revisit.body');
  String get journeyNextExploreTitle =>
      _progressText('journey.next.explore.title');
  String get journeyNextExploreBody =>
      _progressText('journey.next.explore.body');
  String get journeyNextAction => _progressText('journey.next.action');
  String get journeyDetails => _progressText('journey.details');
  String get journeyTimeline => _progressText('journey.timeline');
  String get journeyInitialCommit => _progressText('journey.initial_commit');
  String get journeyLatestDecision => _progressText('journey.latest_decision');
  String get journeyNoUpdate => _progressText('journey.no_update');
  String get journeyReflectionPending =>
      _progressText('journey.reflection_pending');
  String get reportEntryEyebrow => _progressText('report.entry.eyebrow');
  String get reportEntryTitle => _progressText('report.entry.title');
  String get reportEntryBody => _progressText('report.entry.body');
  String get reportEntryAction => _progressText('report.entry.action');
  String get reportTitle => _progressText('report.title');
  String get reportEyebrow => _progressText('report.eyebrow');
  String get reportHeroTitle => _progressText('report.hero_title');
  String get reportHeroSubtitle => _progressText('report.hero_subtitle');
  String get reportPreviewNotice => _progressText('report.preview_notice');
  String get reportSnapshot => _progressText('report.snapshot');
  String get reportDateRange => _progressText('report.date_range');
  String get reportMoments => _progressText('report.moments');
  String get reportEmpty => _progressText('report.empty');
  String get reportInitialCommit => _progressText('report.initial_commit');
  String get reportDecisionUpdate => _progressText('report.decision_update');
  String get reportReflectionCompleted =>
      _progressText('report.reflection_completed');
  String get reportOpenCase => _progressText('report.open_case');
  String get reportNonInference => _progressText('report.non_inference');

  String journeyWeighCount(int count) =>
      _progressText('journey.weigh_count', placeholders: {'count': count});

  String journeyUpdateCount(int count) => _progressText(
    count == 1 ? 'journey.update_count.one' : 'journey.update_count.many',
    placeholders: {'count': count},
  );

  String reportEntryCount(int count) =>
      _progressText('report.entry.count', placeholders: {'count': count});

  String reportRevision(int count) =>
      _progressText('report.revision', placeholders: {'count': count});

  String get accountOfferTitle => _progressText('account.offer.title');
  String get accountOfferBody => _progressText('account.offer.body');
  String get accountOfferUnavailable =>
      _progressText('account.offer.unavailable');
}
