import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/product_preview/atlas_preview_fixture.dart';
import 'package:kefe_mobile/app/product_preview/atlas_preview_screen.dart';
import 'package:kefe_mobile/app/product_preview/preview_content_localizer.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';
import 'package:kefe_mobile/core/localization/kefe_content_localizer.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';

void main() {
  test(
    'Atlas slice 5 contract keeps representative-data boundaries closed',
    () {
      final contractFile = File(
        '../../docs/contracts/premium-atlas-slice5.v1.json',
      );
      expect(contractFile.existsSync(), isTrue);

      final contract =
          jsonDecode(contractFile.readAsStringSync()) as Map<String, Object?>;
      final truthfulness = contract['truthfulness']! as Map<String, Object?>;
      final continuum = contract['continuum']! as Map<String, Object?>;
      final invariants = contract['invariants']! as Map<String, Object?>;

      expect(truthfulness['product_preview_only'], isTrue);
      expect(truthfulness['representative_country_averages_only'], isTrue);
      expect(truthfulness['real_country_result_claim'], isFalse);
      expect(truthfulness['live_update_claim'], isFalse);
      expect(truthfulness['sample_claim'], isFalse);
      expect(truthfulness['inferred_geography'], isFalse);
      expect(truthfulness['three_dimensional_globe_engine'], isFalse);
      expect(continuum['minimum'], 0);
      expect(continuum['maximum'], 10);
      expect(continuum['derived_percentage_split_allowed'], isFalse);
      expect(continuum['additional_metric_allowed'], isFalse);
      expect(invariants['commit_first'], isTrue);
      expect(invariants['blind_first'], isTrue);
      expect(invariants['signal_in_scope'], isFalse);
      expect(invariants['impact_in_scope'], isFalse);
    },
  );

  test(
    'Atlas fixture preserves exact selected Case and representative values',
    () {
      expect(
        AtlasPreviewFixture.selectedCaseId,
        '11111111-1111-4111-8111-111111111112',
      );
      expect(
        AtlasPreviewFixture.countries
            .map((country) => (country.countryCode, country.value))
            .toList(),
        const [
          ('TR', 7.1),
          ('DE', 5.4),
          ('US', 6.2),
          ('JP', 4.8),
          ('BR', 6.7),
          ('ID', 7.3),
        ],
      );
    },
  );

  test('Atlas presentation consumes semantic/localized boundaries', () {
    final source = File(
      'lib/app/product_preview/atlas_preview_screen.dart',
    ).readAsStringSync();

    expect(source, contains('AtlasPreviewStrings.of(context)'));
    expect(source, contains('kefeContentLocalizerProvider'));
    expect(source, contains('KefeContentNamespace.caseTitle'));
    expect(source, contains('KefeSurface('));
    expect(source, contains('CustomPaint('));
    expect(source, contains('ExcludeSemantics('));
    expect(source, isNot(contains('KefeColorTokens.')));
    expect(source, isNot(contains('locale.languageCode')));
    expect(source, isNot(contains('Ülkelere göre ortalamalar')));
    expect(source, isNot(contains('gerçek ülke sonucu değildir')));
    expect(source, isNot(contains('%')));
  });

  testWidgets('Atlas is localized and theme-adaptive in Product Preview', (
    tester,
  ) async {
    Future<void> pump({
      required ThemeData theme,
      required Locale locale,
    }) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            kefeContentLocalizerProvider.overrideWithValue(
              const PreviewContentLocalizer(),
            ),
          ],
          child: MaterialApp(
            theme: theme,
            locale: locale,
            supportedLocales: KefeStrings.supportedLocales,
            localizationsDelegates: const [
              KefeStringsDelegate(),
              GlobalMaterialLocalizations.delegate,
              GlobalWidgetsLocalizations.delegate,
              GlobalCupertinoLocalizations.delegate,
            ],
            home: const Scaffold(body: AtlasPreviewScreen()),
          ),
        ),
      );
      await tester.pumpAndSettle();
    }

    await pump(theme: KefeTheme.light(), locale: const Locale('en', 'US'));
    var context = tester.element(
      find.byKey(const ValueKey('atlas-preview-list')),
    );
    expect(context.kefeVisual.isDark, isFalse);
    expect(find.text('Same question,\ndifferent worlds.'), findsOneWidget);
    expect(
      find.text(
        'Atlas values are representative Product Preview data · not real country results',
      ),
      findsOneWidget,
    );
    expect(
      find.text("Should AI companies' personal data collection be limited?"),
      findsOneWidget,
    );
    expect(find.text('Country averages'), findsOneWidget);
    expect(find.text('Germany'), findsOneWidget);
    expect(find.text('7.1'), findsOneWidget);
    expect(find.text('7.3'), findsOneWidget);

    await pump(theme: KefeTheme.dark(), locale: const Locale('tr', 'TR'));
    context = tester.element(find.byKey(const ValueKey('atlas-preview-list')));
    expect(context.kefeVisual.isDark, isTrue);
    expect(find.text('Aynı soru,\nfarklı dünyalar.'), findsOneWidget);
    expect(
      find.text(
        'Atlas değerleri temsili Product Preview verisidir · gerçek ülke sonucu değildir',
      ),
      findsOneWidget,
    );
    expect(
      find.text(
        'Yapay zekâ şirketlerinin veri toplaması sınırlandırılmalı mı?',
      ),
      findsOneWidget,
    );
    expect(find.text('Ülkelere göre ortalamalar'), findsOneWidget);
    expect(find.text('Almanya'), findsOneWidget);
  });
}
