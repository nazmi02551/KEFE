import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/product_preview/preview_content_localizer.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';
import 'package:kefe_mobile/core/localization/kefe_content_localizer.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';
import 'package:kefe_mobile/features/decision/presentation/reveal_result_card.dart';

const revealFixture = RevealResult(
  layer: 'TRUSTED',
  sampleSize: 18472,
  confidence: 'HIGH',
  values: {'Doğru': 0.57, 'Yanlış': 0.43},
);

Widget revealHarness({
  required ThemeData theme,
  required Locale locale,
  bool disableAnimations = false,
  String selectedOption = 'Yanlış',
}) {
  return ProviderScope(
    overrides: [
      kefeContentLocalizerProvider.overrideWithValue(
        const PreviewContentLocalizer(),
      ),
    ],
    child: MaterialApp(
      theme: theme,
      locale: locale,
      supportedLocales: KefeStrings.supportedLocales,
      localizationsDelegates: const [KefeStringsDelegate()],
      home: MediaQuery(
        data: MediaQueryData(disableAnimations: disableAnimations),
        child: Scaffold(
          body: SingleChildScrollView(
            child: RevealResultCard(
              reveal: revealFixture,
              selectedOption: selectedOption,
            ),
          ),
        ),
      ),
    ),
  );
}

void main() {
  testWidgets(
    'Reveal localizes display labels without changing raw result keys',
    (tester) async {
      await tester.pumpWidget(
        revealHarness(
          theme: KefeTheme.light(),
          locale: const Locale('en', 'US'),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('reveal-card')), findsOneWidget);
      expect(
        find.byKey(const ValueKey('reveal-personal-decision')),
        findsOneWidget,
      );
      expect(find.byKey(const ValueKey('reveal-gap-insight')), findsOneWidget);
      expect(find.byKey(const ValueKey('reveal-methodology')), findsOneWidget);

      expect(find.text('Correct'), findsOneWidget);
      expect(find.text('Incorrect'), findsNWidgets(2));
      expect(find.text('Doğru'), findsNothing);
      expect(find.text('Yanlış'), findsNothing);

      expect(
        find.byKey(const ValueKey(('reveal-option', 'Yanlış'))),
        findsOneWidget,
      );
      expect(revealFixture.values['Doğru'], 0.57);
      expect(revealFixture.values['Yanlış'], 0.43);
    },
  );

  testWidgets('Reveal distribution motion collapses under Reduce Motion', (
    tester,
  ) async {
    await tester.pumpWidget(
      revealHarness(
        theme: KefeTheme.dark(),
        locale: const Locale('tr', 'TR'),
        disableAnimations: true,
      ),
    );
    await tester.pump();

    final context = tester.element(find.byKey(const ValueKey('reveal-card')));
    expect(context.kefeVisual.isDark, isTrue);
    expect(
      KefeMotion.resolve(context, const Duration(milliseconds: 420)),
      Duration.zero,
    );

    final animatedBars = find.byType(TweenAnimationBuilder<double>);
    expect(animatedBars, findsNWidgets(2));
    for (final widget in tester.widgetList<TweenAnimationBuilder<double>>(
      animatedBars,
    )) {
      expect(widget.duration, Duration.zero);
    }
  });
}
