import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:go_router/go_router.dart';

import '../core/design/kefe_theme.dart';
import '../core/localization/kefe_strings.dart';
import '../features/decision/presentation/decision_flow_screen.dart';
import '../features/explore/presentation/explore_screen.dart';

class KefeApp extends StatefulWidget {
  const KefeApp({this.initialLocation = '/explore', super.key});

  final String initialLocation;

  @override
  State<KefeApp> createState() => _KefeAppState();
}

class _KefeAppState extends State<KefeApp> {
  late final GoRouter _router = GoRouter(
    initialLocation: widget.initialLocation,
    routes: [
      GoRoute(path: '/', redirect: (_, _) => '/explore'),
      GoRoute(
        path: '/explore',
        builder: (context, state) => const ExploreScreen(),
      ),
      GoRoute(
        path: '/case/:caseId',
        builder: (context, state) => DecisionFlowScreen(
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
