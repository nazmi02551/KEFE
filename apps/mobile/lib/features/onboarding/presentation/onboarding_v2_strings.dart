import '../../../core/localization/kefe_locale_catalog.dart';
import '../../../core/localization/kefe_strings.dart';

abstract final class OnboardingV2StringCatalog {
  static const KefeLocaleResources resources = {
    'en': {
      'page_one.eyebrow': 'KEFE',
      'page_one.title': 'Weigh your own decision first.',
      'page_one.body':
          'Before any community result appears, look at the question through your own values and commit your answer.',
      'page_two.eyebrow': 'COMPARE WITH THE COMMUNITY',
      'page_two.title': 'See where your decision sits in the community.',
      'page_two.body':
          'The distribution opens only after you commit. It does not classify you; it only compares this decision with other answers.',
      'page_three.eyebrow': 'WIDEN THE VIEW',
      'page_three.title':
          'Explore other perspectives and your decision journey.',
      'page_three.body':
          'Inspect different viewpoints. In reweigh journeys, compare your first and final decisions without KEFE claiming what caused a change.',
      'continue': 'Continue',
      'start': 'Make your first weigh',
    },
    'tr': {
      'page_one.eyebrow': 'KEFE',
      'page_one.title': 'Önce kendi kararını tart.',
      'page_one.body':
          'Topluluk sonucu açılmadan önce konuya kendi değerlerinle bak ve kararını sabitle.',
      'page_two.eyebrow': 'TOPLUMLA KARŞILAŞTIR',
      'page_two.title': 'Kararının toplumdaki yerini gör.',
      'page_two.body':
          'Topluluk dağılımı ancak kararını sabitledikten sonra açılır. Bu görünüm seni sınıflandırmaz; yalnızca bu kararını diğer yanıtlarla karşılaştırır.',
      'page_three.eyebrow': 'BAKIŞINI GENİŞLET',
      'page_three.title': 'Farklı bakışları ve karar yolculuğunu keşfet.',
      'page_three.body':
          'Farklı perspektifleri incele. Yeniden tartım olan yolculuklarda ilk ve son kararını karşılaştır; KEFE değişimin nedenini varsaymaz.',
      'continue': 'Devam et',
      'start': 'İlk tartımı yap',
    },
  };
}

extension OnboardingV2Strings on KefeStrings {
  String _onboardingV2Text(String key) => KefeLocaleCatalog.resolve(
    locale: locale,
    resources: OnboardingV2StringCatalog.resources,
    key: key,
  );

  String get onboardingV2PageOneEyebrow =>
      _onboardingV2Text('page_one.eyebrow');
  String get onboardingV2PageOneTitle => _onboardingV2Text('page_one.title');
  String get onboardingV2PageOneBody => _onboardingV2Text('page_one.body');
  String get onboardingV2PageTwoEyebrow =>
      _onboardingV2Text('page_two.eyebrow');
  String get onboardingV2PageTwoTitle => _onboardingV2Text('page_two.title');
  String get onboardingV2PageTwoBody => _onboardingV2Text('page_two.body');
  String get onboardingV2PageThreeEyebrow =>
      _onboardingV2Text('page_three.eyebrow');
  String get onboardingV2PageThreeTitle =>
      _onboardingV2Text('page_three.title');
  String get onboardingV2PageThreeBody => _onboardingV2Text('page_three.body');
  String get onboardingV2Continue => _onboardingV2Text('continue');
  String get onboardingV2Start => _onboardingV2Text('start');
}
