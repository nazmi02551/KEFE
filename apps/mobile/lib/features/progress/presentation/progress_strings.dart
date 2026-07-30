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

  String journeyWeighCount(int count) =>
      _progressText('journey.weigh_count', placeholders: {'count': count});

  String journeyUpdateCount(int count) => _progressText(
    count == 1 ? 'journey.update_count.one' : 'journey.update_count.many',
    placeholders: {'count': count},
  );

  String get accountOfferTitle => _progressText('account.offer.title');
  String get accountOfferBody => _progressText('account.offer.body');
  String get accountOfferUnavailable =>
      _progressText('account.offer.unavailable');
}
