import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:go_router/go_router.dart';

import '../core/build/preview_build_info.dart';
import '../core/design/kefe_theme.dart';
import '../core/localization/kefe_strings.dart';
import '../features/decision/presentation/decision_flow_screen.dart';
import '../features/explore/presentation/discovery_explore_screen.dart';
import '../features/progress/presentation/my_kefe_journey_screen.dart';
import 'product_preview/atlas_preview_screen.dart';
import 'product_preview/radar_preview_screen.dart';
import 'product_preview/weigh_preview_screen.dart';

class ProductPreviewApp extends StatefulWidget {
  const ProductPreviewApp({super.key});

  @override
  State<ProductPreviewApp> createState() => _ProductPreviewAppState();
}

class _ProductPreviewAppState extends State<ProductPreviewApp> {
  late final GoRouter _router = GoRouter(
    initialLocation: '/explore',
    routes: [
      GoRoute(path: '/', redirect: (_, _) => '/explore'),
      GoRoute(
        path: '/explore',
        builder: (_, _) => const _PreviewShell(
          selectedIndex: 0,
          child: DiscoveryExploreScreen(embedded: true),
        ),
      ),
      GoRoute(
        path: '/radar',
        builder: (_, _) => const _PreviewShell(
          selectedIndex: 1,
          child: RadarPreviewScreen(),
        ),
      ),
      GoRoute(
        path: '/weigh',
        builder: (_, _) => const _PreviewShell(
          selectedIndex: 2,
          child: WeighPreviewScreen(),
        ),
      ),
      GoRoute(
        path: '/atlas',
        builder: (_, _) => const _PreviewShell(
          selectedIndex: 3,
          child: AtlasPreviewScreen(),
        ),
      ),
      GoRoute(
        path: '/my-kefe',
        builder: (_, _) => const _PreviewShell(
          selectedIndex: 4,
          child: MyKefeJourneyScreen(embedded: true),
        ),
      ),
      GoRoute(
        path: '/case/:caseId',
        builder: (_, state) => DecisionFlowScreen(
          caseId: state.pathParameters['caseId']!,
        ),
      ),
    ],
  );

  @override
  void dispose() {
    _router.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'KEFE Product Preview',
      debugShowCheckedModeBanner: false,
      locale: const Locale('tr', 'TR'),
      theme: KefeTheme.light(),
      darkTheme: KefeTheme.dark(),
      themeMode: ThemeMode.dark,
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

class _PreviewShell extends StatelessWidget {
  const _PreviewShell({required this.selectedIndex, required this.child});

  final int selectedIndex;
  final Widget child;

  static const _paths = [
    '/explore',
    '/radar',
    '/weigh',
    '/atlas',
    '/my-kefe',
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: child,
      bottomNavigationBar: DecoratedBox(
        decoration: const BoxDecoration(
          border: Border(top: BorderSide(color: KefeColorTokens.borderDark)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (selectedIndex == 4) const _PreviewBuildIdentity(),
            NavigationBar(
              selectedIndex: selectedIndex,
              onDestinationSelected: (index) => context.go(_paths[index]),
              destinations: const [
                NavigationDestination(
                  icon: Icon(Icons.explore_outlined),
                  selectedIcon: Icon(Icons.explore_rounded),
                  label: 'Keşfet',
                ),
                NavigationDestination(
                  icon: Icon(Icons.radar_outlined),
                  selectedIcon: Icon(Icons.radar_rounded),
                  label: 'Radar',
                ),
                NavigationDestination(
                  icon: _ScaleNavIcon(selected: false),
                  selectedIcon: _ScaleNavIcon(selected: true),
                  label: 'Tartım',
                ),
                NavigationDestination(
                  icon: Icon(Icons.public_outlined),
                  selectedIcon: Icon(Icons.public_rounded),
                  label: 'Atlas',
                ),
                NavigationDestination(
                  icon: Icon(Icons.person_outline_rounded),
                  selectedIcon: Icon(Icons.person_rounded),
                  label: 'Profil',
                ),
              ],
            ),
          ],
        ),
      ),
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

class _ScaleNavIcon extends StatelessWidget {
  const _ScaleNavIcon({required this.selected});

  final bool selected;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 42,
      height: 42,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: selected
            ? KefeColorTokens.gold
            : KefeColorTokens.gold.withValues(alpha: 0.12),
        border: Border.all(
          color: KefeColorTokens.gold.withValues(alpha: 0.55),
        ),
      ),
      child: Icon(
        Icons.balance_rounded,
        color: selected ? const Color(0xFF171106) : KefeColorTokens.goldSoft,
        size: 23,
      ),
    );
  }
}