import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Settings exposes account continuity as an explicit passive entry', () {
    final screen = File(
      'lib/features/settings/presentation/settings_screen.dart',
    ).readAsStringSync();
    final strings = File(
      'lib/core/localization/settings_strings.dart',
    ).readAsStringSync();
    final catalog = File(
      'lib/core/localization/settings_string_catalog.dart',
    ).readAsStringSync();

    expect(screen, contains("ValueKey('settings-account-entry')"));
    expect(screen, contains("context.push('/account')"));
    expect(screen, contains('strings.accountAndContinuity'));
    expect(screen, contains('strings.accountAndContinuityHelper'));
    expect(screen, contains("ValueKey('settings-privacy-entry')"));

    // Merely opening Settings must not start identity/account work.
    expect(screen, isNot(contains('accountControllerProvider')));
    expect(screen, isNot(contains('accountRepositoryProvider')));

    expect(strings, contains('String get accountAndContinuity'));
    expect(strings, contains('String get accountAndContinuityHelper'));
    expect(catalog, contains("'account.title': 'Account and continuity'"));
    expect(catalog, contains("'account.title': 'Hesap ve devamlılık'"));
    expect(catalog, contains('Guest use remains available.'));
    expect(catalog, contains('Misafir olarak kullanmaya devam edebilirsin.'));
  });

  test('production and Product Preview reuse the governed account route', () {
    final productionApp = File('lib/app/kefe_app.dart').readAsStringSync();
    final previewApp = File(
      'lib/app/product_preview_app.dart',
    ).readAsStringSync();
    final accountScreen = File(
      'lib/features/account/presentation/account_conversion_screen.dart',
    ).readAsStringSync();

    for (final app in [productionApp, previewApp]) {
      expect(app, contains("path: '/account'"));
      expect(app, contains('AccountConversionScreen'));
    }

    expect(accountScreen, contains("ValueKey('account-continue-guest')"));
    expect(accountScreen, contains('context.pop()'));
    expect(accountScreen, contains('strings.continueAsGuest'));
  });
}
