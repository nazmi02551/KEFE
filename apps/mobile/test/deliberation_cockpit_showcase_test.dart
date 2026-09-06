import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/presentation/deliberation_cockpit_showcase.dart';

void main() {
  testWidgets('DeliberationCockpitShowcase renders and interacts properly in Turkish', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        locale: Locale('tr', 'TR'),
        supportedLocales: KefeStrings.supportedLocales,
        localizationsDelegates: [
          KefeStringsDelegate(),
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        home: Scaffold(
          body: SingleChildScrollView(
            child: DeliberationCockpitShowcase(),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('deliberation-cockpit-showcase')), findsOneWidget);
    expect(find.byKey(const ValueKey('deliberation-active-title')), findsOneWidget);

    // Initial title should be Sentetik Astroturfing Kalkanı
    expect(find.textContaining('Astroturfing'), findsWidgets);

    // Tap on the second pill (3-Eksenli Etik Denge)
    final secondPill = find.textContaining('3-Eksenli');
    expect(secondPill, findsWidgets);
    await tester.tap(secondPill.first);
    await tester.pumpAndSettle();

    // Now active title should be 3-Eksenli Etik Denge
    expect(find.textContaining('3-Eksenli Etik Denge'), findsWidgets);
  });

  testWidgets('CaseDeliberationBadgesRow renders badges properly in Turkish', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        locale: Locale('tr', 'TR'),
        supportedLocales: KefeStrings.supportedLocales,
        localizationsDelegates: [
          KefeStringsDelegate(),
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        home: Scaffold(
          body: CaseDeliberationBadgesRow(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.textContaining('Bot Kalkanı'), findsWidgets);
    expect(find.textContaining('3-Eksenli'), findsWidgets);
    expect(find.textContaining('Makbuz'), findsWidgets);
    expect(find.textContaining('Esneklik'), findsWidgets);
  });
}
