import 'dart:convert';
import 'dart:io';

import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/kefe_locale_catalog.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/progress/localization/progress_string_catalog.dart';
import 'package:kefe_mobile/features/progress/presentation/progress_strings.dart';

void main() {
  test('Slice 6 contract keeps migration incremental and product boundaries closed', () {
    final file = File(
      '../../docs/contracts/localization-foundation-slice6.v1.json',
    );
    expect(file.existsSync(), isTrue);

    final contract = jsonDecode(file.readAsStringSync()) as Map<String, Object?>;
    final migration = contract['migration']! as Map<String, Object?>;
    final invariants = contract['invariants']! as Map<String, Object?>;

    expect(migration['progress_strings_migrated'], isTrue);
    expect(migration['core_kefe_strings_migrated'], isFalse);
    expect(migration['internal_alpha_strings_migrated'], isFalse);
    expect(migration['repo_wide_localization_complete'], isFalse);
    expect(migration['locale_preference_behavior_change'], isFalse);
    expect(invariants['commit_first'], isTrue);
    expect(invariants['blind_first'], isTrue);
    expect(invariants['signal_in_scope'], isFalse);
    expect(invariants['impact_in_scope'], isFalse);
  });

  test('Progress catalog has exact key parity for current supported languages', () {
    expect(
      KefeLocaleCatalog.missingKeys(ProgressStringCatalog.resources, 'tr'),
      isEmpty,
    );
    expect(
      KefeLocaleCatalog.extraKeys(ProgressStringCatalog.resources, 'tr'),
      isEmpty,
    );
    expect(
      KefeLocaleCatalog.missingKeys(ProgressStringCatalog.resources, 'en'),
      isEmpty,
    );
    expect(
      KefeLocaleCatalog.extraKeys(ProgressStringCatalog.resources, 'en'),
      isEmpty,
    );
  });

  test('resolver falls back to English and interpolates placeholders safely', () {
    expect(
      KefeLocaleCatalog.resolve(
        locale: const Locale('de', 'DE'),
        resources: ProgressStringCatalog.resources,
        key: 'progress.title',
      ),
      'My KEFE',
    );
    expect(
      KefeLocaleCatalog.resolve(
        locale: const Locale('de', 'DE'),
        resources: ProgressStringCatalog.resources,
        key: 'journey.update_count.many',
        placeholders: const {'count': 3},
      ),
      '3 revisits',
    );
    expect(
      KefeLocaleCatalog.resolve(
        locale: const Locale('en', 'US'),
        resources: ProgressStringCatalog.resources,
        key: 'missing.stable.key',
      ),
      'missing.stable.key',
    );
  });

  test('Progress public copy API preserves current TR and EN wording', () {
    const tr = KefeStrings(Locale('tr', 'TR'));
    const en = KefeStrings(Locale('en', 'US'));

    expect(tr.progressTitle, 'Benim Kefem');
    expect(en.progressTitle, 'My KEFE');
    expect(tr.progressReadiness('FORMING'), 'Karar geçmişin oluşmaya başladı.');
    expect(
      en.progressReadiness('FORMING'),
      'Your decision history is beginning to take shape.',
    );
    expect(tr.journeyUpdateCount(1), '1 yeniden tartım');
    expect(tr.journeyUpdateCount(3), '3 yeniden tartım');
    expect(en.journeyUpdateCount(1), '1 revisit');
    expect(en.journeyUpdateCount(3), '3 revisits');
    expect(en.journeyWeighCount(1), '1 weighs');
  });

  test('migrated Progress string getters contain no locale branching', () {
    final source = File(
      'lib/features/progress/presentation/progress_strings.dart',
    ).readAsStringSync();

    expect(source, isNot(contains('locale.languageCode')));
    expect(source, isNot(contains('_isTurkish')));
    expect(source, isNot(contains('languageCode ==')));
    expect(source, contains('KefeLocaleCatalog.resolve'));
    expect(source, contains('ProgressStringCatalog.resources'));
  });
}
