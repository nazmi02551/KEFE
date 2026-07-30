import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/build/preview_build_info.dart';
import '../core/design/kefe_theme.dart';
import '../core/localization/kefe_strings.dart';
import '../core/localization/settings_strings.dart';
import '../core/preferences/app_preferences.dart';
import '../features/account/presentation/account_conversion_screen.dart';
import '../features/activity/presentation/activity_screen.dart';
import '../features/decision/presentation/decision_flow_screen.dart';
import '../features/explore/presentation/discovery_explore_screen.dart';
import '../features/privacy/presentation/privacy_screen.dart';
import '../features/progress/presentation/my_kefe_journey_screen.dart';
import '../features/settings/presentation/settings_screen.dart';
import '../features/sharing/presentation/public_share_screen.dart';
import '../features/weigh/presentation/weigh_hub_screen.dart';
import 'primary_navigation_shell.dart';
import 'product_preview/atlas_preview_screen.dart';
import 'product_preview/radar_preview_screen.dart';

class ProductPreviewApp extends ConsumerStatefulWidget {
  const ProductPreviewApp({super.key});

  @override
  ConsumerState<ProductPreviewApp> createState() => _ProductPreviewAppState();
}

class _ProductPreviewAppState extends ConsumerState<ProductPreviewApp> {
  late final GoRouter _router = GoRouter(
    initialLocation: '/explore',
    routes: [
      GoRoute(path: '/', redirect: (_, _) => '/explore'),
      GoRoute(
        path: '/explore',
        builder: (_, _) => PrimaryNavigationShell(
          selectedIndex: 0,
          floatingActionButton: const _ExploreSecondaryActions(),
          child: const DiscoveryExploreScreen(embedded: true),
        ),
      ),
      GoRoute(
        path: '/weigh',
        builder: (_, _) => const PrimaryNavigationShell(
          selectedIndex: 1,
          child: WeighHubScreen(embedded: true),
        ),
      ),
      GoRoute(
        path: '/activity',
        builder: (_, _) => const PrimaryNavigationShell(
          selectedIndex: 2,
          child: ActivityScreen(embedded: true),
        ),
      ),
      GoRoute(
        path: '/my-kefe',
        builder: (context, _) => PrimaryNavigationShell(
          selectedIndex: 3,
          floatingActionButton: FloatingActionButton.small(
            key: const ValueKey('open-preview-settings'),
            onPressed: () => context.push('/settings'),
            tooltip: KefeStrings.of(context).settingsTitle,
            child: const Icon(Icons.settings_outlined),
          ),
          footer: const _PreviewBuildIdentity(),
          child: const MyKefeJourneyScreen(embedded: true),
        ),
      ),
      GoRoute(path: '/settings', builder: (_, _) => const SettingsScreen()),
      GoRoute(
        path: '/account',
        builder: (_, _) => const AccountConversionScreen(),
      ),
      GoRoute(path: '/privacy', builder: (_, _) => const PrivacyScreen()),
      GoRoute(
        path: '/share/:token',
        builder: (_, state) =>
            PublicShareScreen(token: state.pathParameters['token']!),
      ),
      GoRoute(
        path: '/radar',
        builder: (context, _) => _SecondaryPreviewPage(
          title: 'Radar',
          child: const RadarPreviewScreen(),
          onBack: () => _returnToExplore(context),
        ),
      ),
      GoRoute(
        path: '/atlas',
        builder: (context, _) => _SecondaryPreviewPage(
          title: 'Atlas',
          child: const AtlasPreviewScreen(),
          onBack: () => _returnToExplore(context),
        ),
      ),
      GoRoute(
        path: '/case/:caseId',
        builder: (_, state) =>
            DecisionFlowScreen(caseId: state.pathParameters['caseId']!),
      ),
    ],
  );

  static void _returnToExplore(BuildContext context) {
    if (context.canPop()) {
      context.pop();
    } else {
      context.go('/explore');
    }
  }

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

class _ExploreSecondaryActions extends StatelessWidget {
  const _ExploreSecondaryActions();

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        FloatingActionButton.small(
          key: const ValueKey('open-preview-radar'),
          heroTag: 'preview-radar',
          tooltip: 'Radar',
          onPressed: () => context.push('/radar'),
          child: const Icon(Icons.radar_rounded),
        ),
        const SizedBox(height: 10),
        FloatingActionButton.small(
          key: const ValueKey('open-preview-atlas'),
          heroTag: 'preview-atlas',
          tooltip: 'Atlas',
          onPressed: () => context.push('/atlas'),
          child: const Icon(Icons.public_rounded),
        ),
      ],
    );
  }
}

class _SecondaryPreviewPage extends StatelessWidget {
  const _SecondaryPreviewPage({
    required this.title,
    required this.child,
    required this.onBack,
  });

  final String title;
  final Widget child;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: BackButton(onPressed: onBack),
        title: Text(title),
      ),
      body: child,
    );
  }
}

class _PreviewBuildIdentity extends StatelessWidget {
  const _PreviewBuildIdentity();

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: PreviewBuildInfo.label,
      child: Container(
        key: const ValueKey('preview-build-identity'),
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
        color: KefeColorTokens.surfaceDark,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.verified_outlined,
              size: 14,
              color: KefeColorTokens.goldSoft,
            ),
            const SizedBox(width: 6),
            Flexible(
              child: Text(
                PreviewBuildInfo.label,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                  color: KefeColorTokens.textMutedDark,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
