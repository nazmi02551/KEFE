import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/product_preview/atlas_globe_visual.dart';
import 'package:kefe_mobile/app/product_preview/atlas_preview_fixture.dart';
import 'package:kefe_mobile/app/product_preview/atlas_preview_screen.dart';
import 'package:kefe_mobile/app/product_preview/atlas_preview_strings.dart';
import 'package:kefe_mobile/app/product_preview/preview_components.dart';
import 'package:kefe_mobile/app/product_preview_app.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';

void main() {
  test('Slice 19 contract preserves representative Preview truthfulness', () {
    final contract =
        jsonDecode(
              File(
                '../../docs/contracts/atlas-world-globe-slice19.v1.json',
              ).readAsStringSync(),
            )
            as Map<String, dynamic>;

    expect(contract['contract'], 'atlas-world-globe-slice19');
    expect(contract['route']['preview_path'], '/atlas');
    expect(contract['route']['preview_only'], isTrue);
    expect(contract['route']['production_route_forbidden'], isTrue);
    expect(
      contract['data_truthfulness']['fixture_values_are_representative_preview_only'],
      isTrue,
    );
    expect(
      contract['data_truthfulness']['fixture_values_are_real_country_results'],
      isFalse,
    );
    expect(
      contract['data_truthfulness']['globe_marker_values_source'],
      'AtlasPreviewFixture.countries',
    );
    expect(
      contract['data_truthfulness']['duplicate_globe_value_constants_forbidden'],
      isTrue,
    );
    expect(
      contract['data_truthfulness']['invented_country_percentages_forbidden'],
      isTrue,
    );
    expect(
      contract['data_truthfulness']['invented_sample_size_forbidden'],
      isTrue,
    );
    expect(
      contract['data_truthfulness']['invented_confidence_forbidden'],
      isTrue,
    );
    expect(contract['presentation']['continuous_animation_forbidden'], isTrue);
    expect(contract['presentation']['live_3d_required'], isFalse);
    expect(contract['presentation']['text_scale_safe'], isTrue);
    expect(contract['tests']['globe_marker_fixture_value_parity'], isTrue);
  });

  test('existing Atlas fixture values remain unchanged', () {
    expect(
      AtlasPreviewFixture.countries
          .map((item) => '${item.countryCode}:${item.value.toStringAsFixed(1)}')
          .toList(),
      const ['TR:7.1', 'DE:5.4', 'US:6.2', 'JP:4.8', 'BR:6.7', 'ID:7.3'],
    );
  });

  test('production router still does not expose Atlas', () {
    final productionApp = File('lib/app/kefe_app.dart').readAsStringSync();
    final previewApp = File(
      'lib/app/product_preview_app.dart',
    ).readAsStringSync();

    expect(productionApp, isNot(contains("path: '/atlas'")));
    expect(previewApp, contains("path: '/atlas'"));
    expect(previewApp, contains("ValueKey('open-preview-experiences')"));
  });

  testWidgets(
    'Atlas renders notice, globe, markers and complete country cards',
    (tester) async {
      await _pumpAtlas(tester, ThemeMode.dark);

      final noticeFinder = find.byKey(const ValueKey('atlas-preview-notice'));
      expect(noticeFinder, findsOneWidget);
      expect(
        tester.widget<PreviewNotice>(noticeFinder).text,
        AtlasPreviewStrings.resources['tr']!['notice'],
      );
      expect(find.byKey(const ValueKey('atlas-world-globe')), findsOneWidget);
      expect(
        find.byKey(const ValueKey('atlas-selected-case-title')),
        findsOneWidget,
      );

      final globe = tester.widget<AtlasGlobeVisual>(
        find.byType(AtlasGlobeVisual),
      );
      expect(
        globe.markers
            .map(
              (item) => '${item.countryCode}:${item.value.toStringAsFixed(1)}',
            )
            .toList(),
        AtlasPreviewFixture.countries
            .map(
              (item) => '${item.countryCode}:${item.value.toStringAsFixed(1)}',
            )
            .toList(),
      );
      for (final item in AtlasPreviewFixture.countries) {
        expect(
          find.byKey(ValueKey('atlas-country-marker-${item.countryCode}')),
          findsOneWidget,
        );
      }

      await _revealCountryCards(tester);
      for (final item in AtlasPreviewFixture.countries) {
        expect(
          find.byKey(ValueKey('atlas-country-card-${item.countryCode}')),
          findsOneWidget,
        );
      }

      expect(find.text('7.1'), findsOneWidget);
      expect(find.text('5.4'), findsOneWidget);
      expect(find.text('6.2'), findsOneWidget);
      expect(find.text('4.8'), findsOneWidget);
      expect(find.text('6.7'), findsOneWidget);
      expect(find.text('7.3'), findsOneWidget);
      expect(find.textContaining('%'), findsNothing);
    },
  );

  testWidgets('Atlas remains valid in light theme', (tester) async {
    await _pumpAtlas(tester, ThemeMode.light);

    expect(find.byKey(const ValueKey('atlas-world-globe')), findsOneWidget);
    expect(find.byKey(const ValueKey('atlas-preview-notice')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Atlas compacts without losing truth notice on a narrow phone', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(320, 640));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await _pumpAtlas(tester, ThemeMode.dark);

    expect(
      tester.getSize(find.byKey(const ValueKey('atlas-world-globe'))).height,
      218,
    );
    final noticeFinder = find.byKey(const ValueKey('atlas-preview-notice'));
    expect(noticeFinder, findsOneWidget);
    expect(
      tester.widget<PreviewNotice>(noticeFinder).text,
      AtlasPreviewStrings.resources['tr']!['notice'],
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('Atlas remains usable with enlarged text', (tester) async {
    await tester.binding.setSurfaceSize(const Size(390, 844));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await _pumpAtlas(tester, ThemeMode.dark, textScale: 1.6);

    expect(find.byKey(const ValueKey('atlas-preview-notice')), findsOneWidget);
    expect(find.byKey(const ValueKey('atlas-world-globe')), findsOneWidget);
    await _revealCountryCards(tester);
    for (final item in AtlasPreviewFixture.countries) {
      expect(
        find.byKey(ValueKey('atlas-country-card-${item.countryCode}')),
        findsOneWidget,
      );
    }
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'Product Preview experience hub reaches the Atlas truth surface',
    (tester) async {
      await tester.pumpWidget(const ProviderScope(child: ProductPreviewApp()));
      await tester.pumpAndSettle();

      final experiencesAction = find.byKey(
        const ValueKey('open-preview-experiences'),
      );
      expect(experiencesAction, findsOneWidget);
      await tester.tap(experiencesAction);
      await tester.pumpAndSettle();

      final atlasAction = find.text('Atlas önizlemesini aç');
      expect(atlasAction, findsOneWidget);
      await tester.tap(atlasAction);
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('atlas-preview-list')), findsOneWidget);
      final noticeFinder = find.byKey(const ValueKey('atlas-preview-notice'));
      expect(noticeFinder, findsOneWidget);
      expect(
        AtlasPreviewStrings.resources.values
            .map((catalog) => catalog['notice'])
            .whereType<String>(),
        contains(tester.widget<PreviewNotice>(noticeFinder).text),
      );
      expect(find.byKey(const ValueKey('atlas-world-globe')), findsOneWidget);
    },
  );
}

Future<void> _revealCountryCards(WidgetTester tester) async {
  final lastCard = find.byKey(const ValueKey('atlas-country-card-ID'));
  await tester.scrollUntilVisible(
    lastCard,
    320,
    scrollable: find.byType(Scrollable).first,
  );
  await tester.pump();
}

Future<void> _pumpAtlas(
  WidgetTester tester,
  ThemeMode themeMode, {
  double textScale = 1.0,
}) async {
  await tester.pumpWidget(
    ProviderScope(
      child: MaterialApp(
        locale: const Locale('tr'),
        supportedLocales: KefeStrings.supportedLocales,
        localizationsDelegates: const [
          KefeStringsDelegate(),
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        theme: KefeTheme.light(),
        darkTheme: KefeTheme.dark(),
        themeMode: themeMode,
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(
            context,
          ).copyWith(textScaler: TextScaler.linear(textScale)),
          child: child!,
        ),
        home: const Scaffold(body: AtlasPreviewScreen()),
      ),
    ),
  );
  await tester.pumpAndSettle();
}
