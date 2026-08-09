import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';
import 'package:kefe_mobile/features/decision/presentation/reveal_result_card.dart';

Future<void> pumpResultCard(
  WidgetTester tester, {
  required String layer,
  required String confidence,
}) async {
  await tester.pumpWidget(
    ProviderScope(
      child: MaterialApp(
        locale: const Locale('tr', 'TR'),
        supportedLocales: KefeStrings.supportedLocales,
        localizationsDelegates: const [
          KefeStringsDelegate(),
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        theme: KefeTheme.light(),
        home: Scaffold(
          body: SingleChildScrollView(
            child: RevealResultCard(
              reveal: RevealResult(
                layer: layer,
                sampleSize: 2,
                confidence: confidence,
                values: const {'A': 0.5, 'B': 0.5},
              ),
              selectedOption: 'A',
            ),
          ),
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void expectDistributionRemainsVisible() {
  expect(
    find.byKey(const ValueKey(('reveal-option', 'A'))),
    findsOneWidget,
  );
  expect(
    find.byKey(const ValueKey(('reveal-option', 'B'))),
    findsOneWidget,
  );
  expect(find.byKey(const ValueKey('reveal-methodology')), findsOneWidget);
}

void main() {
  testWidgets('RAW result shows distribution but no KEFE Gap interpretation', (
    tester,
  ) async {
    await pumpResultCard(
      tester,
      layer: 'RAW',
      confidence: 'INSUFFICIENT',
    );

    expectDistributionRemainsVisible();
    expect(find.byKey(const ValueKey('reveal-gap-insight')), findsNothing);
    expect(find.textContaining('Temsiliyet iddiası yok'), findsOneWidget);
  });

  testWidgets('TRUSTED result preserves the existing KEFE Gap insight', (
    tester,
  ) async {
    await pumpResultCard(tester, layer: 'TRUSTED', confidence: 'MEDIUM');

    expectDistributionRemainsVisible();
    expect(find.byKey(const ValueKey('reveal-gap-insight')), findsOneWidget);
    expect(find.textContaining('Güvenilir örneklem'), findsOneWidget);
  });

  testWidgets('unknown result layer fails closed without KEFE Gap insight', (
    tester,
  ) async {
    await pumpResultCard(
      tester,
      layer: 'EXPERIMENTAL',
      confidence: 'INSUFFICIENT',
    );

    expectDistributionRemainsVisible();
    expect(find.byKey(const ValueKey('reveal-gap-insight')), findsNothing);
    expect(find.textContaining('Sonuç katmanı EXPERIMENTAL'), findsOneWidget);
  });
}
