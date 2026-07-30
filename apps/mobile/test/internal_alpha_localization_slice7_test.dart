import 'dart:convert';
import 'dart:io';

import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_string_catalog.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_locale_catalog.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';

void main() {
  test('slice 7 contract keeps localization and product boundaries closed', () {
    final contractFile = File(
      '../../docs/contracts/internal-alpha-localization-slice7.v1.json',
    );
    expect(contractFile.existsSync(), isTrue);

    final contract =
        jsonDecode(contractFile.readAsStringSync()) as Map<String, Object?>;
    final scope = contract['scope']! as Map<String, Object?>;
    final localization = contract['localization']! as Map<String, Object?>;
    final invariants = contract['invariants']! as Map<String, Object?>;

    expect(scope['shared_locale_resolver_reused'], isTrue);
    expect(scope['internal_alpha_strings_migrated'], isTrue);
    expect(scope['core_kefe_strings_migrated'], isFalse);
    expect(scope['third_locale_enabled'], isFalse);
    expect(scope['copy_semantics_changed'], isFalse);
    expect(localization['english_fallback'], isTrue);
    expect(localization['tr_en_key_parity_required'], isTrue);
    expect(localization['presentation_locale_branching_forbidden'], isTrue);
    expect(invariants['commit_first'], isTrue);
    expect(invariants['blind_first'], isTrue);
    expect(invariants['signal_in_scope'], isFalse);
    expect(invariants['impact_in_scope'], isFalse);
    expect(invariants['personality_inference'], isFalse);
  });

  test('Internal Alpha TR and EN catalogs have exact canonical key parity', () {
    final resources = InternalAlphaStringCatalog.resources;

    expect(KefeLocaleCatalog.missingKeys(resources, 'en'), isEmpty);
    expect(KefeLocaleCatalog.extraKeys(resources, 'en'), isEmpty);
    expect(KefeLocaleCatalog.missingKeys(resources, 'tr'), isEmpty);
    expect(KefeLocaleCatalog.extraKeys(resources, 'tr'), isEmpty);
    expect(resources['tr']!.keys.toSet(), resources['en']!.keys.toSet());
  });

  test('unknown locale falls back to English without becoming supported', () {
    final strings = KefeStrings(const Locale('fr', 'FR'));

    expect(strings.primaryNavExplore, 'Explore');
    expect(strings.accountTitle, 'Protect your history');
    expect(
      strings.accountCodeInstruction('user@example.com'),
      'Enter the 6-digit code sent to user@example.com.',
    );
    expect(strings.consensusStanceLabel('AGREE'), 'Agree');
    expect(strings.domainName('TECHNOLOGY_AI'), 'Technology');
    expect(
      KefeStrings.supportedLocales,
      const [Locale('tr', 'TR'), Locale('en', 'US')],
    );
  });

  test('Internal Alpha public behavior preserves Turkish and English copy', () {
    final tr = KefeStrings(const Locale('tr', 'TR'));
    final en = KefeStrings(const Locale('en', 'US'));

    expect(tr.primaryNavExplore, 'Keşfet');
    expect(en.primaryNavExplore, 'Explore');
    expect(tr.accountReturnMyKefe, 'My KEFE’ye dön');
    expect(en.accountReturnMyKefe, 'Return to My KEFE');
    expect(tr.activityUpdateCount(1), '1 yeniden tartım');
    expect(tr.activityUpdateCount(3), '3 yeniden tartım');
    expect(en.activityUpdateCount(1), '1 decision update');
    expect(en.activityUpdateCount(3), '3 decision updates');
    expect(
      tr.consensusUnavailable('TEMP'),
      'Konsensüs geçici olarak kullanılamıyor · TEMP',
    );
    expect(
      en.consensusUnavailable(null),
      'Consensus temporarily unavailable',
    );
    expect(tr.consensusReasonLimit(3), 'Gerekçeni en fazla 3 etiketle belirt');
    expect(en.consensusReasonLimit(3), 'Choose up to 3 reason tags');
  });

  test('semantic code mappings and unknown-code fallbacks are preserved', () {
    final tr = KefeStrings(const Locale('tr', 'TR'));
    final en = KefeStrings(const Locale('en', 'US'));

    expect(tr.consensusStanceLabel('DISAGREE'), 'Katılmıyorum');
    expect(en.consensusReasonLabel('PRACTICAL_IMPACT'), 'Practical impact');
    expect(tr.domainName('CITY_PUBLIC_LIFE'), 'Kamusal');
    expect(en.domainName('WORK_BUSINESS'), 'Work & Economy');
    expect(tr.domainName('NEW_DOMAIN'), 'NEW DOMAIN');
    expect(en.confidenceLabel('VERY_HIGH'), 'VERY HIGH');
  });

  test('result placeholders and methodology formatting remain unchanged', () {
    final tr = KefeStrings(const Locale('tr', 'TR'));
    final en = KefeStrings(const Locale('en', 'US'));

    expect(
      tr.gapInsight(selectedIsTop: true, percent: 61),
      'Seçimin toplulukta en yüksek paya sahip. Katılımcıların %61 kadarı aynı seçeneği tercih etti.',
    );
    expect(
      en.gapInsight(selectedIsTop: false, percent: 39),
      'Your choice is not the community majority. 39% of participants chose the same option.',
    );
    expect(
      tr.gapDifferenceInsight(selectedPercent: 37, gapPoints: 18),
      'Seçtiğin seçenek toplulukta %37. En yüksek paya sahip seçenekle fark 18 yüzde puan.',
    );
    expect(
      en.balanceSemantics('Option A'),
      'KEFE balance. Option A',
    );
    expect(
      tr.resultMethodology(sampleSize: 120, confidence: 'HIGH'),
      'Güvenilir örneklem · n=120 · Yüksek güven',
    );
    expect(
      en.resultMethodology(sampleSize: 120, confidence: 'MEDIUM'),
      'Trusted sample · n=120 · Medium confidence',
    );
  });

  test('Internal Alpha presentation source has no direct locale selection', () {
    final source = File(
      'lib/core/localization/internal_alpha_strings.dart',
    ).readAsStringSync();

    expect(source, contains('KefeLocaleCatalog.resolve'));
    expect(source, contains('InternalAlphaStringCatalog.resources'));
    expect(source, isNot(contains('locale.languageCode')));
    expect(source, isNot(contains('_iaTr')));
    expect(source, isNot(contains("'Keşfet'")));
    expect(source, isNot(contains("'Explore'")));
    expect(source, isNot(contains("'Katılıyorum'")));
    expect(source, isNot(contains("'Agree'")));
  });
}
