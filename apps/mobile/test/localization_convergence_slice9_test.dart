import 'dart:convert';
import 'dart:io';

import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/product_preview/atlas_preview_strings.dart';
import 'package:kefe_mobile/app/product_preview/radar_preview_strings.dart';
import 'package:kefe_mobile/core/localization/explore_string_catalog.dart';
import 'package:kefe_mobile/core/localization/explore_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_locale_catalog.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/core/localization/settings_string_catalog.dart';
import 'package:kefe_mobile/core/localization/settings_strings.dart';

void main() {
  test('slice 9 contract keeps convergence boundaries closed', () {
    final contractFile = File(
      '../../docs/contracts/localization-convergence-slice9.v1.json',
    );
    expect(contractFile.existsSync(), isTrue);

    final contract =
        jsonDecode(contractFile.readAsStringSync()) as Map<String, Object?>;
    final scope = contract['scope']! as Map<String, Object?>;
    final localization = contract['localization']! as Map<String, Object?>;
    final audit = contract['audit']! as Map<String, Object?>;
    final invariants = contract['invariants']! as Map<String, Object?>;

    expect(scope['settings_migrated'], isTrue);
    expect(scope['explore_migrated'], isTrue);
    expect(scope['radar_shared_resolver_converged'], isTrue);
    expect(scope['atlas_shared_resolver_converged'], isTrue);
    expect(scope['preview_content_localizer_migrated'], isFalse);
    expect(scope['third_locale_enabled'], isFalse);
    expect(localization['shared_locale_resolver_required'], isTrue);
    expect(localization['supported_locales_remain_tr_en'], isTrue);
    expect(audit['preview_content_localizer_excluded_as_content_seam'], isTrue);
    expect(invariants['commit_first'], isTrue);
    expect(invariants['blind_first'], isTrue);
    expect(invariants['signal_in_scope'], isFalse);
    expect(invariants['impact_in_scope'], isFalse);
  });

  test('Settings and Explore catalogs have exact TR/EN key parity', () {
    for (final resources in [
      SettingsStringCatalog.resources,
      ExploreStringCatalog.resources,
    ]) {
      expect(KefeLocaleCatalog.missingKeys(resources, 'en'), isEmpty);
      expect(KefeLocaleCatalog.extraKeys(resources, 'en'), isEmpty);
      expect(KefeLocaleCatalog.missingKeys(resources, 'tr'), isEmpty);
      expect(KefeLocaleCatalog.extraKeys(resources, 'tr'), isEmpty);
      expect(resources['tr']!.keys.toSet(), resources['en']!.keys.toSet());
    }
  });

  test('Settings and Explore public behavior stays unchanged', () {
    final tr = KefeStrings(const Locale('tr', 'TR'));
    final en = KefeStrings(const Locale('en', 'US'));
    final fr = KefeStrings(const Locale('fr', 'FR'));

    expect(tr.settingsTitle, 'Ayarlar');
    expect(en.settingsTitle, 'Settings');
    expect(tr.languageSystem, 'Cihaz dilini kullan');
    expect(en.themeDark, 'Dark');
    expect(tr.languageTurkish, 'Türkçe');
    expect(en.languageTurkish, 'Türkçe');
    expect(fr.settingsTitle, 'Settings');

    expect(tr.exploreTrendingWeighs, 'Trend tartımlar');
    expect(en.exploreTrendingWeighs, 'Trending weighs');
    expect(tr.exploreCaseCount(1), '1 vaka');
    expect(en.exploreCaseCount(1), '1 cases');
    expect(tr.domainLabel('TECHNOLOGY_AI'), 'Teknoloji & YZ');
    expect(en.domainLabel('WORK_BUSINESS'), 'Work & Economy');
    expect(en.domainLabel('NEW_DOMAIN'), 'NEW DOMAIN');
    expect(fr.exploreWorldQuestion, 'What is the world\nweighing today?');
  });

  test('Radar and Atlas catalogs keep TR/EN parity and English fallback', () {
    for (final resources in [
      RadarPreviewStrings.resources,
      AtlasPreviewStrings.resources,
    ]) {
      expect(KefeLocaleCatalog.missingKeys(resources, 'en'), isEmpty);
      expect(KefeLocaleCatalog.extraKeys(resources, 'en'), isEmpty);
      expect(KefeLocaleCatalog.missingKeys(resources, 'tr'), isEmpty);
      expect(KefeLocaleCatalog.extraKeys(resources, 'tr'), isEmpty);
      expect(resources['tr']!.keys.toSet(), resources['en']!.keys.toSet());
    }

    expect(
      KefeLocaleCatalog.resolve(
        locale: const Locale('fr', 'FR'),
        resources: RadarPreviewStrings.resources,
        key: 'notice',
      ),
      'Not live trend data · Representative ranking for Product Preview',
    );
    expect(
      KefeLocaleCatalog.resolve(
        locale: const Locale('fr', 'FR'),
        resources: AtlasPreviewStrings.resources,
        key: 'country.DE',
      ),
      'Germany',
    );
  });

  test('governed presentation localization consumes the shared resolver', () {
    final governed = {
      'lib/core/localization/kefe_strings.dart': false,
      'lib/core/localization/internal_alpha_strings.dart': true,
      'lib/features/progress/presentation/progress_strings.dart': true,
      'lib/core/localization/settings_strings.dart': true,
      'lib/core/localization/explore_strings.dart': true,
      'lib/app/product_preview/radar_preview_strings.dart': true,
      'lib/app/product_preview/atlas_preview_strings.dart': true,
    };

    for (final entry in governed.entries) {
      final source = File(entry.key).readAsStringSync();
      expect(source, contains('KefeLocaleCatalog.resolve'), reason: entry.key);
      expect(source, isNot(contains('_isTurkish')), reason: entry.key);
      expect(source, isNot(contains('_iaTr')), reason: entry.key);
      expect(source, isNot(contains('bool get _tr')), reason: entry.key);
      expect(
        source,
        isNot(contains('_catalog[locale.languageCode]')),
        reason: entry.key,
      );
      if (entry.value) {
        expect(source, isNot(contains('locale.languageCode')), reason: entry.key);
      }
    }

    final core = File(
      'lib/core/localization/kefe_strings.dart',
    ).readAsStringSync();
    expect(
      core,
      contains("const {'tr', 'en'}.contains(locale.languageCode)"),
    );
    expect(
      KefeStrings.supportedLocales,
      const [Locale('tr', 'TR'), Locale('en', 'US')],
    );
  });
}
