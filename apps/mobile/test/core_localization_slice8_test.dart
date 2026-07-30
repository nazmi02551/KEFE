import 'dart:convert';
import 'dart:io';

import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/core_string_catalog.dart';
import 'package:kefe_mobile/core/localization/kefe_locale_catalog.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';

void main() {
  test('slice 8 contract keeps core localization boundaries closed', () {
    final contractFile = File(
      '../../docs/contracts/core-localization-slice8.v1.json',
    );
    expect(contractFile.existsSync(), isTrue);

    final contract =
        jsonDecode(contractFile.readAsStringSync()) as Map<String, Object?>;
    final scope = contract['scope']! as Map<String, Object?>;
    final localization = contract['localization']! as Map<String, Object?>;
    final invariants = contract['invariants']! as Map<String, Object?>;

    expect(scope['core_kefe_strings_migrated'], isTrue);
    expect(scope['public_kefe_strings_api_preserved'], isTrue);
    expect(scope['delegate_behavior_preserved'], isTrue);
    expect(scope['third_locale_enabled'], isFalse);
    expect(scope['copy_semantics_changed'], isFalse);
    expect(localization['english_fallback'], isTrue);
    expect(localization['tr_en_key_parity_required'], isTrue);
    expect(localization['direct_locale_copy_branching_forbidden'], isTrue);
    expect(localization['supported_locales_remain_tr_en'], isTrue);
    expect(invariants['commit_first'], isTrue);
    expect(invariants['blind_first'], isTrue);
    expect(invariants['signal_in_scope'], isFalse);
    expect(invariants['impact_in_scope'], isFalse);
  });

  test('core TR and EN catalogs have exact canonical key parity', () {
    final resources = CoreStringCatalog.resources;

    expect(KefeLocaleCatalog.missingKeys(resources, 'en'), isEmpty);
    expect(KefeLocaleCatalog.extraKeys(resources, 'en'), isEmpty);
    expect(KefeLocaleCatalog.missingKeys(resources, 'tr'), isEmpty);
    expect(KefeLocaleCatalog.extraKeys(resources, 'tr'), isEmpty);
    expect(resources['tr']!.keys.toSet(), resources['en']!.keys.toSet());
  });

  test('unknown locale falls back to English without becoming supported', () {
    final strings = KefeStrings(const Locale('fr', 'FR'));
    const delegate = KefeStringsDelegate();

    expect(strings.promise, 'Weigh your decision. See why people differ.');
    expect(strings.contextTitle, 'Context');
    expect(strings.contextSourceKind('OTHER'), 'Other source');
    expect(strings.perspectiveTitle, 'See other perspectives');
    expect(delegate.isSupported(const Locale('fr', 'FR')), isFalse);
    expect(delegate.isSupported(const Locale('tr', 'TR')), isTrue);
    expect(delegate.isSupported(const Locale('en', 'US')), isTrue);
    expect(
      KefeStrings.supportedLocales,
      const [Locale('tr', 'TR'), Locale('en', 'US')],
    );
  });

  test('representative core Turkish and English copy stays unchanged', () {
    final tr = KefeStrings(const Locale('tr', 'TR'));
    final en = KefeStrings(const Locale('en', 'US'));

    expect(tr.promise, 'Kararını tart. Farklı düşünmenin nedenlerini gör.');
    expect(en.promise, 'Weigh your decision. See why people differ.');
    expect(tr.onboardingTryCase, 'İlk tartımı yap');
    expect(en.onboardingTryCase, 'Make your first weigh');
    expect(tr.contextUnavailable,
        'Bağlam şu anda yüklenemedi. Sonuç veya topluluk bilgisi gösterilmedi.');
    expect(en.commitHelper, 'Lock your decision and reveal the result.');
    expect(tr.trustedSample, 'Güvenilir örneklem');
    expect(en.trustedSample, 'Trusted sample');
    expect(tr.perspectiveMethodology, 'Bu görünüm hakkında');
    expect(en.perspectiveMethodology, 'About this view');
  });

  test('dynamic placeholders preserve current output exactly', () {
    final tr = KefeStrings(const Locale('tr', 'TR'));
    final en = KefeStrings(const Locale('en', 'US'));

    expect(tr.reasonSelectionLimit(4), 'En fazla 4 gerekçe seçebilirsin.');
    expect(en.reasonSelectionLimit(4), 'You can choose up to 4 reasons.');
    expect(
      tr.reflectionDecisionSummary(true, 2),
      'İki kararın arasında 2 yanıt değişti.',
    );
    expect(
      en.reflectionDecisionSummary(true, 2),
      '2 response changed between your two decisions.',
    );
    expect(
      tr.reflectionInterventionSummary(3),
      'İki kararın arasında 3 kayıtlı karşılaşma bulunuyor.',
    );
    expect(
      en.reflectionInterventionSummary(3),
      '3 recorded encounter sits between the two decisions.',
    );
  });

  test('semantic status code and enum mappings are preserved', () {
    final tr = KefeStrings(const Locale('tr', 'TR'));
    final en = KefeStrings(const Locale('en', 'US'));

    expect(tr.contextClaimStatus('VERIFIED'), 'Doğrulandı');
    expect(en.contextClaimStatus('NEW_STATUS'), 'NEW_STATUS');
    expect(tr.contextSourceKind('EDITORIAL'), 'Editoryal kaynak');
    expect(en.contextSourceKind('UNKNOWN_KIND'), 'Other source');
    expect(tr.reasonTagLabel('PROPORTIONALITY'), 'Orantılılık');
    expect(en.reasonTagLabel('NEW_REASON'), 'NEW REASON');
    expect(
      tr.flowCapabilityPendingBody('FLOW_DECISION_REVISION_REQUIRED'),
      'Bu akışta yeniden tartım adımı var. Karar değişimi altyapısı tamamlandığında aynı akış içinde açılacak.',
    );
    expect(
      en.perspectiveSlotLabel(PerspectiveSlot.alternativeContext),
      'Alternative context',
    );
    expect(tr.perspectiveSourceLabel('CURATED'), 'Editoryal olarak derlendi');
    expect(en.perspectiveSourceLabel('UNKNOWN'), 'Source information');
    expect(
      tr.messageForCode('NETWORK_TIMEOUT'),
      'Bağlantı kurulamadı. Cihazdaki karar korunuyor.',
    );
    expect(
      en.messageForCode('UNKNOWN_ERROR'),
      'Something went wrong. Your decision was not lost; you can retry.',
    );
  });

  test('core presentation source no longer branches copy by locale', () {
    final source = File(
      'lib/core/localization/kefe_strings.dart',
    ).readAsStringSync();

    expect(source, contains('KefeLocaleCatalog.resolve'));
    expect(source, contains('CoreStringCatalog.resources'));
    expect(source, isNot(contains('bool get _tr')));
    expect(source, isNot(contains("'Bağlam'")));
    expect(source, isNot(contains("'Context'")));
    expect(source, isNot(contains("'Doğrulandı'")));
    expect(source, isNot(contains("'Verified'")));
    expect(source, contains("const {'tr', 'en'}.contains(locale.languageCode)"));
  });
}
