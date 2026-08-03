import '../../../core/localization/kefe_locale_catalog.dart';
import '../../../core/localization/kefe_strings.dart';

abstract final class DecisionJourneyStringCatalog {
  static const KefeLocaleResources resources = {
    'en': {
      'active.eyebrow': 'CURRENT STEP',
      'active.helper':
          'Complete this focused step to let the verified journey open what comes next.',
      'active.progress': '{current}/{total}',
      'active.context': 'Review the case before you continue',
      'active.decision': 'Now weigh your own decision',
      'active.result': 'Compare your decision with the community',
      'active.reflection': 'Look back at your decision journey',
      'active.default': 'Continue the decision journey',
      'context_advance.action': 'I reviewed it — continue',
      'context_advance.helper':
          'The next step opens only after you choose to continue.',
      'perspective_disclosure.title':
          'Your result is clear. Now widen the view.',
      'perspective_disclosure.body':
          'Inspect different perspectives without changing or resending the decision you committed.',
      'perspective_disclosure.action': 'See different perspectives',
      'unavailable': 'This journey step is not available right now.',
    },
    'tr': {
      'active.eyebrow': 'ŞİMDİKİ ADIM',
      'active.helper':
          'Bu odak adımını tamamladığında doğrulanmış karar yolculuğu sıradaki aşamayı açar.',
      'active.progress': '{current}/{total}',
      'active.context': 'Devam etmeden önce olayı incele',
      'active.decision': 'Şimdi kendi kararını tart',
      'active.result': 'Kararını toplumla karşılaştır',
      'active.reflection': 'Karar yolculuğuna yeniden bak',
      'active.default': 'Karar yolculuğuna devam et',
      'context_advance.action': 'İnceledim — devam et',
      'context_advance.helper':
          'Sıradaki adım ancak sen devam etmeyi seçtiğinde açılır.',
      'perspective_disclosure.title':
          'Sonucun netleşti. Şimdi bakışını genişlet.',
      'perspective_disclosure.body':
          'Sabitlediğin kararı değiştirmeden veya yeniden göndermeden farklı bakış açılarını incele.',
      'perspective_disclosure.action': 'Farklı bakışları gör',
      'unavailable': 'Bu karar yolculuğu adımı şu anda kullanılamıyor.',
    },
  };
}

extension DecisionJourneyStrings on KefeStrings {
  String _journeyText(
    String key, {
    Map<String, Object?> placeholders = const {},
  }) => KefeLocaleCatalog.resolve(
    locale: locale,
    resources: DecisionJourneyStringCatalog.resources,
    key: key,
    placeholders: placeholders,
  );

  String get activeJourneyEyebrow => _journeyText('active.eyebrow');
  String get activeJourneyHelper => _journeyText('active.helper');
  String activeJourneyProgress(int current, int total) => _journeyText(
    'active.progress',
    placeholders: {'current': current, 'total': total},
  );
  String activeJourneyTitle(String primitiveCode) => switch (primitiveCode) {
    'CONTEXT' => _journeyText('active.context'),
    'DECISION' => _journeyText('active.decision'),
    'COLLECTIVE_RESULT' => _journeyText('active.result'),
    'REFLECTION' => _journeyText('active.reflection'),
    _ => _journeyText('active.default'),
  };

  String get contextAdvanceAction => _journeyText('context_advance.action');
  String get contextAdvanceHelper => _journeyText('context_advance.helper');
  String get perspectiveDisclosureTitle =>
      _journeyText('perspective_disclosure.title');
  String get perspectiveDisclosureBody =>
      _journeyText('perspective_disclosure.body');
  String get perspectiveDisclosureAction =>
      _journeyText('perspective_disclosure.action');
  String get activeJourneyUnavailable => _journeyText('unavailable');
}
