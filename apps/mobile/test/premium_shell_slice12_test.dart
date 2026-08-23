import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:kefe_mobile/app/primary_navigation_shell.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';

void main() {
  test('slice 12 contract preserves canonical shell boundaries', () {
    final contractFile = File(
      '../../docs/contracts/premium-shell-slice12.v1.json',
    );
    expect(contractFile.existsSync(), isTrue);

    final contract =
        jsonDecode(contractFile.readAsStringSync()) as Map<String, Object?>;
    final scope = contract['scope']! as Map<String, Object?>;
    final navigation = contract['navigation']! as Map<String, Object?>;
    final presentation = contract['presentation']! as Map<String, Object?>;
    final invariants = contract['invariants']! as Map<String, Object?>;

    expect(scope['primary_navigation_visual_convergence'], isTrue);
    expect(scope['route_architecture_change'], isFalse);
    expect(scope['new_primary_tab'], isFalse);
    expect(scope['backend_model_change'], isFalse);
    expect(navigation['canonical_destination_count'], 4);
    expect(navigation['canonical_paths'], [
      '/explore',
      '/weigh',
      '/activity',
      '/my-kefe',
    ]);
    expect(navigation['selected_index_semantics_preserved'], isTrue);
    expect(navigation['radar_atlas_secondary_only'], isTrue);
    expect(presentation['semantic_kefe_roles_required'], isTrue);
    expect(presentation['light_dark_parity_required'], isTrue);
    expect(presentation['tr_en_rendering_required'], isTrue);
    expect(presentation['direct_dark_only_tokens_forbidden'], isTrue);
    expect(presentation['new_user_facing_copy'], isFalse);
    expect(invariants['commit_first'], isTrue);
    expect(invariants['blind_first'], isTrue);
    expect(invariants['preview_production_isolation'], isTrue);
    expect(invariants['my_kefe_observed_descriptive_only'], isTrue);
    expect(invariants['personality_inference'], isFalse);
    expect(invariants['causal_inference'], isFalse);
    expect(invariants['signal_in_scope'], isFalse);
    expect(invariants['impact_in_scope'], isFalse);
  });

  test('primary navigation paths remain canonical', () {
    expect(PrimaryNavigationShell.paths, [
      '/explore',
      '/weigh',
      '/activity',
      '/my-kefe',
    ]);
  });

  for (final locale in const [Locale('tr', 'TR'), Locale('en', 'US')]) {
    for (final dark in const [false, true]) {
      testWidgets(
        'primary shell renders four semantic destinations in ${locale.languageCode} ${dark ? 'dark' : 'light'}',
        (tester) async {
          final labels = locale.languageCode == 'tr'
              ? const ['Keşfet', 'Tartım', 'Aktivite', 'My KEFE']
              : const ['Explore', 'Weigh', 'Activity', 'My KEFE'];
          final expectedVisual = dark
              ? KefeVisualTheme.dark
              : KefeVisualTheme.light;

          await _pumpShell(
            tester,
            locale: locale,
            dark: dark,
            floatingActionButton: KefeShellAction(
              actionKey: const ValueKey('slice12-shell-action'),
              icon: Icons.settings_outlined,
              tooltip: 'KEFE',
              onPressed: () {},
            ),
          );

          expect(
            find.byKey(const ValueKey('primary-navigation')),
            findsOneWidget,
          );
          expect(find.byType(NavigationDestination), findsNWidgets(4));
          for (final label in labels) {
            expect(find.text(label), findsOneWidget);
          }

          final surface = tester.widget<DecoratedBox>(
            find.byKey(const ValueKey('primary-navigation-surface')),
          );
          final decoration = surface.decoration as BoxDecoration;
          expect(decoration.color, expectedVisual.surfaceRaised);
          expect(decoration.boxShadow, isNotEmpty);

          final action = tester.widget<FloatingActionButton>(
            find.byKey(const ValueKey('slice12-shell-action')),
          );
          expect(action.backgroundColor, expectedVisual.surfaceStrong);
          expect(action.foregroundColor, expectedVisual.goldSoft);
          expect(
            tester.getSize(find.byKey(const ValueKey('slice12-shell-action'))),
            const Size(48, 48),
          );
          expect(tester.takeException(), isNull);
        },
      );
    }
  }

  testWidgets(
    'canonical tab selection keeps route and selectedIndex semantics',
    (tester) async {
      final router = GoRouter(
        initialLocation: '/explore',
        routes: [
          for (
            var index = 0;
            index < PrimaryNavigationShell.paths.length;
            index++
          )
            GoRoute(
              path: PrimaryNavigationShell.paths[index],
              builder: (_, _) => PrimaryNavigationShell(
                selectedIndex: index,
                child: Center(child: Text('screen-$index')),
              ),
            ),
        ],
      );
      addTearDown(router.dispose);

      await tester.pumpWidget(
        MaterialApp.router(
          locale: const Locale('en', 'US'),
          supportedLocales: KefeStrings.supportedLocales,
          localizationsDelegates: const [
            KefeStringsDelegate(),
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          theme: KefeTheme.light(),
          routerConfig: router,
        ),
      );
      await tester.pumpAndSettle();

      final labels = ['Explore', 'Weigh', 'Activity', 'My KEFE'];
      for (var index = 1; index < labels.length; index++) {
        await tester.tap(find.text(labels[index]));
        await tester.pumpAndSettle();
        expect(find.text('screen-$index'), findsOneWidget);
        expect(
          tester
              .widget<NavigationBar>(
                find.byKey(const ValueKey('primary-navigation')),
              )
              .selectedIndex,
          index,
        );
      }

      await tester.tap(find.text(labels.first));
      await tester.pumpAndSettle();
      expect(find.text('screen-0'), findsOneWidget);
      expect(
        tester
            .widget<NavigationBar>(
              find.byKey(const ValueKey('primary-navigation')),
            )
            .selectedIndex,
        0,
      );
    },
  );

  test('governed shell chrome rejects direct dark-only token dependencies', () {
    final paths = [
      'lib/app/primary_navigation_shell.dart',
      'lib/app/product_preview_app.dart',
    ];

    for (final path in paths) {
      final source = File(path).readAsStringSync();
      expect(source, isNot(contains('KefeColorTokens.surfaceDark')));
      expect(source, isNot(contains('KefeColorTokens.borderDark')));
      expect(source, isNot(contains('KefeColorTokens.textMutedDark')));
    }

    final previewSource = File(
      'lib/app/product_preview_app.dart',
    ).readAsStringSync();
    expect(previewSource, contains('PreviewBuildInfo.label'));
    expect(previewSource, contains("ValueKey('preview-build-identity')"));
    expect(previewSource, contains("ValueKey('open-preview-experiences')"));
    expect(previewSource, isNot(contains("ValueKey('open-preview-radar')")));
    expect(previewSource, isNot(contains("ValueKey('open-preview-atlas')")));
    expect(previewSource, contains("ValueKey('open-preview-settings')"));
  });
}

Future<void> _pumpShell(
  WidgetTester tester, {
  required Locale locale,
  required bool dark,
  Widget? floatingActionButton,
}) async {
  tester.platformDispatcher.localeTestValue = locale;
  addTearDown(tester.platformDispatcher.clearLocaleTestValue);

  await tester.pumpWidget(
    MaterialApp(
      locale: locale,
      supportedLocales: KefeStrings.supportedLocales,
      localizationsDelegates: const [
        KefeStringsDelegate(),
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      theme: KefeTheme.light(),
      darkTheme: KefeTheme.dark(),
      themeMode: dark ? ThemeMode.dark : ThemeMode.light,
      home: PrimaryNavigationShell(
        selectedIndex: 2,
        floatingActionButton: floatingActionButton,
        child: const Center(child: Text('content')),
      ),
    ),
  );
  await tester.pumpAndSettle();
}
