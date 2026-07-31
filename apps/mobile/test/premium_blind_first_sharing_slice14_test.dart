import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:kefe_mobile/core/design/kefe_surface.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/sharing/application/share_controller.dart';
import 'package:kefe_mobile/features/sharing/data/preview_share_repository.dart';
import 'package:kefe_mobile/features/sharing/data/share_repository.dart';
import 'package:kefe_mobile/features/sharing/presentation/public_share_screen.dart';
import 'package:kefe_mobile/features/sharing/presentation/share_section.dart';

void main() {
  test('slice 14 contract locks case-only Blind First sharing boundaries', () {
    final contractFile = File(
      '../../docs/contracts/premium-blind-first-sharing-slice14.v1.json',
    );
    expect(contractFile.existsSync(), isTrue);

    final contract =
        jsonDecode(contractFile.readAsStringSync()) as Map<String, Object?>;
    final scope = contract['scope']! as Map<String, Object?>;
    final blindFirst = contract['blind_first']! as Map<String, Object?>;
    final outbound = contract['outbound']! as Map<String, Object?>;
    final inbound = contract['inbound']! as Map<String, Object?>;
    final presentation = contract['presentation']! as Map<String, Object?>;
    final invariants = contract['invariants']! as Map<String, Object?>;

    expect(scope['outbound_share_visual_convergence'], isTrue);
    expect(scope['inbound_public_share_visual_convergence'], isTrue);
    expect(scope['community_product_expansion'], isFalse);
    expect(scope['share_backend_change'], isFalse);
    expect(scope['share_schema_change'], isFalse);
    expect(blindFirst['share_feature_gate_preserved'], isTrue);
    expect(blindFirst['outbound_include_decision'], isFalse);
    expect(blindFirst['preview_rejects_decision_exposure'], isTrue);
    expect(blindFirst['receiver_enters_case_before_reveal'], isTrue);
    expect(blindFirst['pre_commit_reveal_forbidden'], isTrue);
    expect(blindFirst['sender_decision_forbidden'], isTrue);
    expect(blindFirst['sender_confidence_forbidden'], isTrue);
    expect(blindFirst['sender_reason_forbidden'], isTrue);
    expect(blindFirst['community_result_forbidden'], isTrue);
    expect(outbound['deep_link_prefix'], 'kefe:///share/');
    expect(inbound['weigh_route_pattern'], '/case/:caseId');
    expect(inbound['public_share_fields'], [
      'id',
      'caseId',
      'caseVersionId',
      'title',
      'summary',
      'primaryDomain',
      'createdAt',
      'expiresAt',
    ]);
    expect(presentation['semantic_kefe_surfaces_required'], isTrue);
    expect(presentation['direct_dark_only_tokens_forbidden'], isTrue);
    expect(invariants['commit_first'], isTrue);
    expect(invariants['blind_first'], isTrue);
    expect(invariants['preview_production_isolation'], isTrue);
    expect(invariants['personality_inference'], isFalse);
    expect(invariants['causal_inference'], isFalse);
    expect(invariants['signal_in_scope'], isFalse);
    expect(invariants['impact_in_scope'], isFalse);
  });

  testWidgets('outbound share remains hidden while feature gate is disabled', (
    tester,
  ) async {
    await _pumpLocalized(
      tester,
      locale: const Locale('en', 'US'),
      dark: false,
      child: const Scaffold(body: ShareSection(sessionId: 'session-1')),
    );

    expect(find.byKey(const ValueKey('share-section')), findsNothing);
    expect(find.byKey(const ValueKey('share-create')), findsNothing);
  });

  for (final locale in const [Locale('tr', 'TR'), Locale('en', 'US')]) {
    for (final dark in const [false, true]) {
      testWidgets(
        'outbound case-only share renders create and ready states in ${locale.languageCode} ${dark ? 'dark' : 'light'}',
        (tester) async {
          final repository = PreviewShareRepository();

          await _pumpLocalized(
            tester,
            locale: locale,
            dark: dark,
            sharingEnabled: true,
            repository: repository,
            child: const Scaffold(body: ShareSection(sessionId: 'session-1')),
          );

          expect(find.byKey(const ValueKey('share-section')), findsOneWidget);
          expect(find.byKey(const ValueKey('share-create')), findsOneWidget);
          expect(find.byKey(const ValueKey('share-deep-link')), findsNothing);

          await tester.tap(find.byKey(const ValueKey('share-create')));
          await tester.pumpAndSettle();

          expect(find.byKey(const ValueKey('share-create')), findsNothing);
          expect(find.byKey(const ValueKey('share-deep-link')), findsOneWidget);
          expect(find.byKey(const ValueKey('share-copy')), findsOneWidget);
          expect(find.byKey(const ValueKey('share-revoke')), findsOneWidget);
          expect(
            tester
                .widget<SelectableText>(
                  find.byKey(const ValueKey('share-deep-link')),
                )
                .data,
            startsWith('kefe:///share/'),
          );
          expect(
            tester
                .widget<KefeSurface>(
                  find.byKey(const ValueKey('share-section')),
                )
                .tone,
            KefeSurfaceTone.raised,
          );
          expect(
            tester
                .widget<KefeSurface>(
                  find.byKey(const ValueKey('share-ready-surface')),
                )
                .tone,
            KefeSurfaceTone.sunken,
          );
          expect(
            Theme.of(
              tester.element(find.byKey(const ValueKey('share-section'))),
            ).brightness,
            dark ? Brightness.dark : Brightness.light,
          );
          expect(tester.takeException(), isNull);
        },
      );
    }
  }

  for (final locale in const [Locale('tr', 'TR'), Locale('en', 'US')]) {
    for (final dark in const [false, true]) {
      testWidgets(
        'inbound public share stays case-only in ${locale.languageCode} ${dark ? 'dark' : 'light'}',
        (tester) async {
          final repository = PreviewShareRepository();
          final expectedVisual = dark
              ? KefeVisualTheme.dark
              : KefeVisualTheme.light;

          await _pumpShareRouter(
            tester,
            locale: locale,
            dark: dark,
            repository: repository,
          );

          expect(
            find.byKey(const ValueKey('public-share-screen')),
            findsOneWidget,
          );
          expect(
            find.byKey(const ValueKey('public-share-case-surface')),
            findsOneWidget,
          );
          expect(
            find.byKey(const ValueKey('public-share-blind-first-surface')),
            findsOneWidget,
          );
          expect(
            find.byKey(const ValueKey('public-share-title')),
            findsOneWidget,
          );
          expect(
            find.byKey(const ValueKey('public-share-weigh')),
            findsOneWidget,
          );
          expect(find.byKey(const ValueKey('reveal-card')), findsNothing);

          final appBar = tester.widget<AppBar>(find.byType(AppBar));
          expect(appBar.backgroundColor, expectedVisual.surfaceRaised);
          expect(appBar.foregroundColor, expectedVisual.foreground);
          expect(tester.takeException(), isNull);
        },
      );
    }
  }

  testWidgets('inbound weigh CTA preserves receiver Case route before Reveal', (
    tester,
  ) async {
    await _pumpShareRouter(
      tester,
      locale: const Locale('en', 'US'),
      dark: false,
      repository: PreviewShareRepository(),
    );

    expect(find.byKey(const ValueKey('reveal-card')), findsNothing);
    await tester.tap(find.byKey(const ValueKey('public-share-weigh')));
    await tester.pumpAndSettle();

    expect(find.text('receiver-case-sentinel'), findsOneWidget);
    expect(find.byKey(const ValueKey('reveal-card')), findsNothing);
  });

  test('runtime sources keep share payload and controller Blind First', () {
    final controllerSource = File(
      'lib/features/sharing/application/share_controller.dart',
    ).readAsStringSync();
    final previewSource = File(
      'lib/features/sharing/data/preview_share_repository.dart',
    ).readAsStringSync();
    final repositorySource = File(
      'lib/features/sharing/data/share_repository.dart',
    ).readAsStringSync();

    expect(controllerSource, contains('includeDecision: false'));
    expect(previewSource, contains('if (includeDecision)'));
    expect(previewSource, contains('SHARE_DECISION_EXPOSURE_NOT_SUPPORTED'));

    final publicShareSource = repositorySource.split('class PublicShare').last;
    for (final forbidden in const [
      'decision',
      'confidence',
      'reason',
      'reveal',
      'community',
      'expert',
      'history',
    ]) {
      expect(publicShareSource.toLowerCase(), isNot(contains(forbidden)));
    }
  });

  test('governed share presentation rejects direct dark-only token debt', () {
    for (final path in const [
      'lib/features/sharing/presentation/share_section.dart',
      'lib/features/sharing/presentation/public_share_screen.dart',
    ]) {
      final source = File(path).readAsStringSync();
      expect(source, contains('kefeVisual'));
      expect(source, isNot(contains('KefeColorTokens.surfaceDark')));
      expect(source, isNot(contains('KefeColorTokens.borderDark')));
      expect(source, isNot(contains('KefeColorTokens.textMutedDark')));
    }
  });
}

Future<void> _pumpLocalized(
  WidgetTester tester, {
  required Locale locale,
  required bool dark,
  required Widget child,
  bool sharingEnabled = false,
  ShareRepository? repository,
}) async {
  tester.platformDispatcher.localeTestValue = locale;
  addTearDown(tester.platformDispatcher.clearLocaleTestValue);

  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        if (sharingEnabled)
          shareExperienceEnabledProvider.overrideWithValue(true),
        if (repository != null)
          shareRepositoryProvider.overrideWithValue(repository),
      ],
      child: MaterialApp(
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
        home: child,
      ),
    ),
  );
  await tester.pumpAndSettle();
}

Future<void> _pumpShareRouter(
  WidgetTester tester, {
  required Locale locale,
  required bool dark,
  required ShareRepository repository,
}) async {
  tester.platformDispatcher.localeTestValue = locale;
  addTearDown(tester.platformDispatcher.clearLocaleTestValue);

  final router = GoRouter(
    initialLocation: '/share/inbound-slice14',
    routes: [
      GoRoute(
        path: '/share/:token',
        builder: (_, state) =>
            PublicShareScreen(token: state.pathParameters['token']!),
      ),
      GoRoute(
        path: '/case/:caseId',
        builder: (_, _) =>
            const Scaffold(body: Center(child: Text('receiver-case-sentinel'))),
      ),
    ],
  );
  addTearDown(router.dispose);

  await tester.pumpWidget(
    ProviderScope(
      overrides: [shareRepositoryProvider.overrideWithValue(repository)],
      child: MaterialApp.router(
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
        routerConfig: router,
      ),
    ),
  );
  await tester.pumpAndSettle();
}
