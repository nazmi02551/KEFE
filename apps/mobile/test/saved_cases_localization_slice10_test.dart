import 'dart:convert';
import 'dart:io';

import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/kefe_locale_catalog.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/saved_cases/localization/saved_case_string_catalog.dart';
import 'package:kefe_mobile/features/saved_cases/presentation/saved_case_strings.dart';

void main() {
  test('slice 10 contract keeps residual migration boundaries closed', () {
    final contractFile = File(
      '../../docs/contracts/saved-cases-localization-slice10.v1.json',
    );
    expect(contractFile.existsSync(), isTrue);

    final contract =
        jsonDecode(contractFile.readAsStringSync()) as Map<String, Object?>;
    final scope = contract['scope']! as Map<String, Object?>;
    final localization = contract['localization']! as Map<String, Object?>;
    final audit = contract['audit']! as Map<String, Object?>;
    final invariants = contract['invariants']! as Map<String, Object?>;

    expect(scope['saved_cases_migrated'], isTrue);
    expect(scope['final_presentation_audit'], isTrue);
    expect(scope['preview_content_localizer_migrated'], isFalse);
    expect(scope['third_locale_enabled'], isFalse);
    expect(localization['shared_locale_resolver_required'], isTrue);
    expect(localization['supported_locales_remain_tr_en'], isTrue);
    expect(audit['repo_wide_presentation_scan_required'], isTrue);
    expect(audit['mainline_completion_requires_stack_merge'], isTrue);
    expect(invariants['commit_first'], isTrue);
    expect(invariants['blind_first'], isTrue);
    expect(invariants['signal_in_scope'], isFalse);
    expect(invariants['impact_in_scope'], isFalse);
  });

  test('Saved Cases TR and EN catalogs have exact key parity', () {
    final resources = SavedCaseStringCatalog.resources;

    expect(KefeLocaleCatalog.missingKeys(resources, 'en'), isEmpty);
    expect(KefeLocaleCatalog.extraKeys(resources, 'en'), isEmpty);
    expect(KefeLocaleCatalog.missingKeys(resources, 'tr'), isEmpty);
    expect(KefeLocaleCatalog.extraKeys(resources, 'tr'), isEmpty);
    expect(resources['tr']!.keys.toSet(), resources['en']!.keys.toSet());
  });

  test('Saved Cases public copy and English fallback stay unchanged', () {
    final tr = KefeStrings(const Locale('tr', 'TR'));
    final en = KefeStrings(const Locale('en', 'US'));
    final fr = KefeStrings(const Locale('fr', 'FR'));

    expect(tr.savedCasesTitle, 'Kaydettiklerin');
    expect(en.savedCasesTitle, 'Saved Cases');
    expect(tr.savedCasesSubtitle, 'Daha sonra tartmak için ayırdığın vakalar.');
    expect(en.savedCasesEmpty, 'You have not saved a Case yet.');
    expect(tr.savedCasesOpen, 'Vakayı aç');
    expect(en.savedCasesRemove, 'Remove from saved');
    expect(tr.savedCasesSave, 'Daha sonra için kaydet');
    expect(en.exploreSearchHint, 'Search Case title or summary');
    expect(tr.exploreSavedOnly, 'Yalnızca kaydettiklerim');
    expect(en.exploreClearFilters, 'Clear filters');
    expect(fr.savedCasesTitle, 'Saved Cases');
    expect(fr.exploreDiscoveryLabel, 'Discover Cases');
  });

  test('Saved Cases source consumes shared resolver without locale branch', () {
    final source = File(
      'lib/features/saved_cases/presentation/saved_case_strings.dart',
    ).readAsStringSync();

    expect(source, contains('KefeLocaleCatalog.resolve'));
    expect(source, contains('SavedCaseStringCatalog.resources'));
    expect(source, isNot(contains('_savedCaseIsTurkish')));
    expect(source, isNot(contains('locale.languageCode')));
    expect(source, isNot(contains("'Kaydettiklerin'")));
    expect(source, isNot(contains("'Saved Cases'")));
  });

  test(
    'repo presentation source has only intentional language-code boundaries',
    () {
      final directLanguageFiles = <String>{};
      final forbiddenHelperFiles = <String>{};

      for (final entity in Directory('lib').listSync(recursive: true)) {
        if (entity is! File || !entity.path.endsWith('.dart')) continue;
        final source = entity.readAsStringSync();

        if (source.contains('locale.languageCode')) {
          directLanguageFiles.add(entity.path);
        }
        if (source.contains('_isTurkish') ||
            source.contains('_iaTr') ||
            source.contains('_savedCaseIsTurkish') ||
            source.contains('bool get _tr')) {
          forbiddenHelperFiles.add(entity.path);
        }
      }

      expect(directLanguageFiles, {
        'lib/app/product_preview/preview_content_localizer.dart',
        'lib/core/localization/kefe_locale_catalog.dart',
        'lib/core/localization/kefe_strings.dart',
      });
      expect(forbiddenHelperFiles, isEmpty);
      expect(KefeStrings.supportedLocales, const [
        Locale('tr', 'TR'),
        Locale('en', 'US'),
      ]);
    },
  );
}
