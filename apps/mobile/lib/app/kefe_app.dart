import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:go_router/go_router.dart';

import '../core/design/kefe_theme.dart';
import '../core/localization/kefe_strings.dart';
import '../features/decision/presentation/decision_flow_screen.dart';
import '../features/explore/presentation/explore_screen.dart';
import '../features/onboarding/presentation/onboarding_gate_screen.dart';
import '../features/progress/presentation/my_kefe_journey_screen.dart';

class KefeApp extends StatefulWidget {
  const KefeApp({this.initialLocation = '/welcome', super.key});

  final String initialLocation;

  @override
  State<KefeApp> createState() => _KefeAppState();
}

class _KefeAppState extends State<KefeApp> {
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
        builder: (context, state) => const ExploreScreen(),
      ),
      GoRoute(
        path: '/my-kefe',
        builder: (context, state) => Scaffold(
          appBar: AppBar(
            leading: BackButton(
              onPressed: () {
                if (context.canPop()) {
                  context.pop();
                } else {
                  context.go('/explore');
                }
              },
            ),
            title: const Text('My KEFE'),
          ),
          body: const MyKefeJourneyScreen(embedded: true),
        ),
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
  void dispose() {
    _router.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'KEFE',
      debugShowCheckedModeBanner: false,
      theme: KefeTheme.light(),
      darkTheme: KefeTheme.dark(),
      themeMode: ThemeMode.system,
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
