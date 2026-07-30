import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/product_preview/preview_content_localizer.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';
import 'package:kefe_mobile/core/localization/kefe_content_localizer.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';
import 'package:kefe_mobile/features/decision/presentation/kefe_balance_visual.dart';
import 'package:kefe_mobile/features/decision/presentation/question_input.dart';

void main() {
  testWidgets('signature balance is theme-adaptive and Reduce Motion safe', (
    tester,
  ) async {
    Future<void> pump({
      required ThemeData theme,
      bool disableAnimations = false,
    }) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: theme,
          locale: const Locale('en', 'US'),
          supportedLocales: KefeStrings.supportedLocales,
          localizationsDelegates: const [KefeStringsDelegate()],
          home: MediaQuery(
            data: MediaQueryData(disableAnimations: disableAnimations),
            child: const Scaffold(
              body: KefeBalanceVisual(
                leftLabel: 'Rules / Rights',
                rightLabel: 'Empathy / Compassion',
                selectedIndex: 1,
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
    }

    await pump(theme: KefeTheme.light());
    var context = tester.element(find.byKey(const ValueKey('kefe-balance-visual')));
    expect(context.kefeVisual.isDark, isFalse);
    expect(find.text('Rules / Rights'), findsOneWidget);
    expect(find.text('Empathy / Compassion'), findsOneWidget);

    await pump(theme: KefeTheme.dark(), disableAnimations: true);
    context = tester.element(find.byKey(const ValueKey('kefe-balance-visual')));
    expect(context.kefeVisual.isDark, isTrue);
    expect(
      KefeMotion.resolve(context, const Duration(milliseconds: 360)),
      Duration.zero,
    );
  });

  testWidgets('localized option labels preserve raw decision values', (
    tester,
  ) async {
    Object? captured;
    const question = DecisionQuestion(
      id: '33333333-3333-4333-8333-333333333335',
      prompt: 'Hakemin penaltı kararını nasıl değerlendiriyorsun?',
      responseType: 'SINGLE_CHOICE',
      options: ['Doğru', 'Yanlış'],
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          kefeContentLocalizerProvider.overrideWithValue(
            const PreviewContentLocalizer(),
          ),
        ],
        child: MaterialApp(
          theme: KefeTheme.light(),
          locale: const Locale('en', 'US'),
          supportedLocales: KefeStrings.supportedLocales,
          localizationsDelegates: const [KefeStringsDelegate()],
          home: Scaffold(
            body: QuestionInputCard(
              question: question,
              value: null,
              enabled: true,
              onChanged: (value) => captured = value,
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(
      find.text("How do you assess the referee's penalty decision?"),
      findsOneWidget,
    );
    expect(find.text('Correct'), findsAtLeastNWidgets(1));
    expect(find.text('Incorrect'), findsAtLeastNWidgets(1));

    await tester.tap(find.byKey(const ValueKey('option-Doğru')));
    await tester.pump();
    expect(captured, 'Doğru');
  });

  test('preview content catalog falls back without mutating Turkish fixture data', () {
    const localizer = PreviewContentLocalizer();
    const caseId = '11111111-1111-4111-8111-111111111113';

    expect(
      localizer.text(
        namespace: KefeContentNamespace.caseTitle,
        id: caseId,
        locale: const Locale('en', 'US'),
        fallback: 'Bu pozisyonda penaltı kararı doğru muydu?',
      ),
      'Was the penalty decision correct?',
    );
    expect(
      localizer.text(
        namespace: KefeContentNamespace.option,
        id: 'Doğru',
        locale: const Locale('tr', 'TR'),
        fallback: 'Doğru',
      ),
      'Doğru',
    );
  });
}
