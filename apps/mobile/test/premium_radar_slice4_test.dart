import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/product_preview/preview_content_localizer.dart';
import 'package:kefe_mobile/app/product_preview/radar_preview_fixture.dart';
import 'package:kefe_mobile/app/product_preview/radar_preview_screen.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';
import 'package:kefe_mobile/core/localization/kefe_content_localizer.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';

void main() {
  test('Radar slice 4 contract keeps preview truthfulness boundaries closed', () {
    final contractFile = File('../../docs/contracts/premium-radar-slice4.v1.json');
    expect(contractFile.existsSync(), isTrue);

    final contract =
        jsonDecode(contractFile.readAsStringSync()) as Map<String, Object?>;
    final truthfulness = contract['truthfulness']! as Map<String, Object?>;
    final localization = contract['localization']! as Map<String, Object?>;
    final runtime = contract['runtime']! as Map<String, Object?>;
    final invariants = contract['invariants']! as Map<String, Object?>;

    expect(truthfulness['product_preview_only'], isTrue);
    expect(truthfulness['representative_ranking_only'], isTrue);
    expect(truthfulness['live_trend_claim'], isFalse);
    expect(truthfulness['personalization_claim'], isFalse);
    expect(
      truthfulness['for_you_label_allowed_without_personalization'],
      isFalse,
    );
    expect(localization['catalog_keyed_by_locale_and_string_id'], isTrue);
    expect(localization['presentation_locale_branching_forbidden'], isTrue);
    expect(runtime['canonical_case_route_preserved'], isTrue);
    expect(runtime['stable_case_ids_preserved'], isTrue);
    expect(runtime['case_specific_runtime_added'], isFalse);
    expect(invariants['commit_first'], isTrue);
    expect(invariants['blind_first'], isTrue);
    expect(invariants['signal_in_scope'], isFalse);
    expect(invariants['impact_in_scope'], isFalse);
    expect(invariants['personality_inference'], isFalse);
  });

  test('Radar fixture keeps canonical stable Case ids', () {
    expect(RadarPreviewFixture.items, hasLength(5));
    expect(
      RadarPreviewFixture.items.map((item) => item.caseId).toSet(),
      {
        '11111111-1111-4111-8111-111111111112',
        '11111111-1111-4111-8111-111111111113',
        '11111111-1111-4111-8111-111111111117',
        '11111111-1111-4111-8111-111111111116',
        '11111111-1111-4111-8111-111111111118',
      },
    );
  });

  test('Radar presentation consumes semantic/localized boundaries', () {
    final source = File(
      'lib/app/product_preview/radar_preview_screen.dart',
    ).readAsStringSync();

    expect(source, contains('RadarPreviewStrings.of(context)'));
    expect(source, contains('kefeContentLocalizerProvider'));
    expect(source, contains('KefeContentNamespace.caseTitle'));
    expect(source, contains('KefeSurface('));
    expect(source, contains("context.push('/case/\${item.caseId}')"));
    expect(source, isNot(contains('KefeColorTokens.')));
    expect(source, isNot(contains('locale.languageCode')));
    expect(source, isNot(contains('Senin için')));
    expect(source, isNot(contains('For you')));
    expect(source, isNot(contains('Canlı trend verisi değil')));
  });

  testWidgets('Radar is localized and theme-adaptive in Product Preview', (
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
            localizationsDelegates: const [KefeStringsDelegate()],
            home: const Scaffold(body: RadarPreviewScreen()),
          ),
        ),
      );
      await tester.pumpAndSettle();
    }

    await pump(theme: KefeTheme.light(), locale: const Locale('en', 'US'));
    var context = tester.element(find.byKey(const ValueKey('radar-preview-list')));
    expect(context.kefeVisual.isDark, isFalse);
    expect(find.text('KEFE RADAR'), findsOneWidget);
    expect(find.text('What is the world\nweighing right now?'), findsOneWidget);
    expect(
      find.text('Not live trend data · Representative ranking for Product Preview'),
      findsOneWidget,
    );
    expect(find.text('Trends'), findsOneWidget);
    expect(find.text('Rising'), findsOneWidget);
    expect(find.text('Global'), findsOneWidget);
    expect(find.text('For you'), findsNothing);
    expect(
      find.text("Should AI companies' personal data collection be limited?"),
      findsOneWidget,
    );

    await pump(theme: KefeTheme.dark(), locale: const Locale('tr', 'TR'));
    context = tester.element(find.byKey(const ValueKey('radar-preview-list')));
    expect(context.kefeVisual.isDark, isTrue);
    expect(find.text('Dünya şu an\nneyi tartışıyor?'), findsOneWidget);
    expect(
      find.text(
        'Canlı trend verisi değil · Product Preview için temsili sıralama',
      ),
      findsOneWidget,
    );
    expect(find.text('Senin için'), findsNothing);
    expect(
      find.text('Yapay zekâ şirketlerinin veri toplaması sınırlandırılmalı mı?'),
      findsOneWidget,
    );
  });
}
