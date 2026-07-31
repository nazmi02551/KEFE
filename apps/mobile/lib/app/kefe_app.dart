import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/design/kefe_theme.dart';
import '../core/localization/kefe_strings.dart';
import '../core/localization/settings_strings.dart';
import '../core/preferences/app_preferences.dart';
import '../features/account/presentation/account_conversion_screen.dart';
import '../features/activity/presentation/activity_screen.dart';
import '../features/decision/presentation/decision_flow_screen.dart';
import '../features/explore/presentation/discovery_explore_screen.dart';
import '../features/onboarding/presentation/onboarding_gate_screen.dart';
import '../features/privacy/presentation/privacy_screen.dart';
import '../features/progress/presentation/my_kefe_journey_screen.dart';
import '../features/settings/presentation/settings_screen.dart';
import '../features/sharing/presentation/public_share_screen.dart';
import '../features/weigh/presentation/weigh_hub_screen.dart';
import 'primary_navigation_shell.dart';

class KefeApp extends ConsumerStatefulWidget {
  const KefeApp({this.initialLocation = '/welcome', super.key});

  final String initialLocation;

  @override
  ConsumerState<KefeApp> createState() => _KefeAppState();
}

class _KefeAppState extends ConsumerState<KefeApp> {
  late final GoRouter _router = GoRouter(
    initialLocation: widget.initialLocation,
    routes: [
      GoRoute(path: '/', redirect: (_, _) => '/welcome'),
      GoRoute(
        path: '/welcome',
        builder: (context, state) => const OnboardingGateScreen(),
      ),
      GoRoute(
        path: '/explore',
        builder: (context, state) => const PrimaryNavigationShell(
          selectedIndex: 0,
          child: DiscoveryExploreScreen(embedded: true),
        ),
      ),
      GoRoute(
        path: '/weigh',
        builder: (context, state) => const PrimaryNavigationShell(
          selectedIndex: 1,
          child: WeighHubScreen(embedded: true),
        ),
      ),
      GoRoute(
        path: '/activity',
        builder: (context, state) => const PrimaryNavigationShell(
          selectedIndex: 2,
          child: ActivityScreen(embedded: true),
        ),
      ),
      GoRoute(
        path: '/my-kefe',
        builder: (context, state) => PrimaryNavigationShell(
          selectedIndex: 3,
          floatingActionButton: KefeShellAction(
            actionKey: const ValueKey('open-settings'),
            icon: Icons.settings_outlined,
            tooltip: KefeStrings.of(context).settingsTitle,
            onPressed: () => context.push('/settings'),
          ),
          child: const MyKefeJourneyScreen(embedded: true),
        ),
      ),
      GoRoute(
        path: '/account',
        builder: (context, state) => const AccountConversionScreen(),
      ),
      GoRoute(
        path: '/settings',
        builder: (context, state) => const SettingsScreen(),
      ),
      GoRoute(
        path: '/privacy',
        builder: (context, state) => const PrivacyScreen(),
      ),
      GoRoute(
        path: '/share/:token',
        builder: (context, state) =>
            PublicShareScreen(token: state.pathParameters['token']!),
      ),
      GoRoute(
        path: '/case/:caseId',
        builder: (context, state) => DecisionFlowScreen(
          caseId: state.pathParameters['caseId']!,
          firstUse: state.uri.queryParameters['firstUse'] == '1',
        ),
      ),
    ],
  );

  @override
  void initState() {
    super.initState();
    Future<void>.microtask(
      () => ref.read(appPreferencesControllerProvider.notifier).load(),
    );
  }

  @override
  void dispose() {
    _router.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final preferences = ref.watch(appPreferencesControllerProvider);
    return MaterialApp.router(
      title: 'KEFE',
      debugShowCheckedModeBanner: false,
      locale: preferences.resolvedLocale,
      theme: KefeTheme.light(),
      darkTheme: KefeTheme.dark(),
      themeMode: preferences.resolvedThemeMode,
      routerConfig: _router,
      supportedLocales: KefeStrings.supportedLocales,
      localizationsDelegates: const [
        KefeStringsDelegate(),
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
    );
  }
}
