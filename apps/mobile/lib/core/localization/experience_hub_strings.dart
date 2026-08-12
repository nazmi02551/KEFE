import 'experience_hub_string_catalog.dart';
import 'kefe_locale_catalog.dart';
import 'kefe_strings.dart';

extension KefeExperienceHubStrings on KefeStrings {
  String _experienceText(String key) => KefeLocaleCatalog.resolve(
    locale: locale,
    resources: ExperienceHubStringCatalog.resources,
    key: key,
  );

  String get experienceHubTitle => _experienceText('title');
  String get experienceHubSubtitle => _experienceText('subtitle');
  String get experienceHubOpen => _experienceText('open');
  String get experienceStandardTitle => _experienceText('standard_title');
  String get experienceStandardBody => _experienceText('standard_body');
  String get experienceStandardAction => _experienceText('standard_action');
  String get experienceSportsTitle => _experienceText('sports_title');
  String get experienceSportsBody => _experienceText('sports_body');
  String get experienceSportsAction => _experienceText('sports_action');
  String get experienceSportsEmpty => _experienceText('sports_empty');
  String get experienceRadarTitle => _experienceText('radar_title');
  String get experienceRadarBody => _experienceText('radar_body');
  String get experienceRadarAction => _experienceText('radar_action');
  String get experiencePreviewStatus => _experienceText('preview_status');
  String get experienceAtlasTitle => _experienceText('atlas_title');
  String get experienceAtlasBody => _experienceText('atlas_body');
  String get experienceAtlasAction => _experienceText('atlas_action');
  String get experienceAtlasStatus => _experienceText('atlas_status');
  String get experienceProductionTruthNote =>
      _experienceText('production_truth_note');
  String get experiencePreviewTruthNote => _experienceText('preview_truth_note');
  String get experienceLoading => _experienceText('loading');
  String get experienceRetry => _experienceText('retry');
}
