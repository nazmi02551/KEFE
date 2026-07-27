import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:go_router/go_router.dart';

import '../core/design/kefe_theme.dart';
import '../core/localization/kefe_strings.dart';
import '../features/decision/presentation/decision_flow_screen.dart';

final _router = GoRouter(
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const DecisionFlowScreen(),
    ),
  ],
);

class KefeApp extends StatelessWidget {
  const KefeApp({super.key});

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
