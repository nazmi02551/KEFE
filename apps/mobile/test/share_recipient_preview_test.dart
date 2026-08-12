import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/sharing/application/share_controller.dart';
import 'package:kefe_mobile/features/sharing/data/preview_share_repository.dart';
import 'package:kefe_mobile/features/sharing/presentation/public_share_screen.dart';
import 'package:kefe_mobile/features/sharing/presentation/share_section.dart';

void main() {
  testWidgets('sender can preview the case-only recipient journey', (tester) async {
    final repository = PreviewShareRepository();
    final router = GoRouter(
      initialLocation: '/sender',
      routes: [
        GoRoute(
          path: '/sender',
          builder: (_, _) => const Scaffold(
            body: SingleChildScrollView(
              child: ShareSection(sessionId: 'preview-session'),
            ),
          ),
        ),
        GoRoute(
          path: '/share/:token',
          builder: (_, state) =>
              PublicShareScreen(token: state.pathParameters['token']!),
        ),
      ],
    );
    addTearDown(router.dispose);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          shareExperienceEnabledProvider.overrideWithValue(true),
          shareRepositoryProvider.overrideWithValue(repository),
        ],
        child: MaterialApp.router(
          locale: const Locale('tr', 'TR'),
          supportedLocales: KefeStrings.supportedLocales,
          localizationsDelegates: const [
            KefeStringsDelegate(),
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          routerConfig: router,
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('share-create')), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('share-create')));
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('share-ready-surface')), findsOneWidget);
    expect(
      find.byKey(const ValueKey('share-external-entry-boundary')),
      findsOneWidget,
    );

    await tester.tap(find.byKey(const ValueKey('share-preview-receiver')));
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('public-share-screen')), findsOneWidget);
    expect(find.byKey(const ValueKey('public-share-case-surface')), findsOneWidget);
    expect(
      find.byKey(const ValueKey('public-share-blind-first-surface')),
      findsOneWidget,
    );
    expect(find.byKey(const ValueKey('public-share-weigh')), findsOneWidget);
  });
}
