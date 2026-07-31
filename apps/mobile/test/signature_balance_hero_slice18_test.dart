import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';
import 'package:kefe_mobile/features/decision/presentation/kefe_balance_visual.dart';
import 'package:kefe_mobile/features/decision/presentation/question_input.dart';

void main() {
  test('Slice 18 contract preserves binary decision truthfulness', () {
    final contract =
        jsonDecode(
              File(
                '../../docs/contracts/signature-balance-hero-slice18.v1.json',
              ).readAsStringSync(),
            )
            as Map<String, dynamic>;

    expect(contract['contract'], 'signature-balance-hero-slice18');
    expect(contract['eligibility']['response_type'], 'SINGLE_CHOICE');
    expect(contract['eligibility']['required_option_count'], 2);
    expect(contract['scope']['question_response_semantics_change'], isFalse);
    expect(contract['scope']['case_specific_branching'], isFalse);
    expect(contract['truthfulness']['canonical_option_values_unchanged'], isTrue);
    expect(contract['truthfulness']['invented_percentage_for_binary_forbidden'], isTrue);
    expect(contract['truthfulness']['pre_commit_collective_exposure_forbidden'], isTrue);
    expect(contract['presentation']['continuous_animation_forbidden'], isTrue);
    expect(contract['foundation_reuse']['same_widget_in_production_and_preview'], isTrue);
  });

  testWidgets('exactly two SINGLE_CHOICE options use the signature balance', (
    tester,
  ) async {
    Object? submitted;
    await _pumpQuestion(
      tester,
      question: const DecisionQuestion(
        id: 'binary',
        prompt: 'Choose one',
        responseType: 'SINGLE_CHOICE',
        options: ['LEFT_RAW', 'RIGHT_RAW'],
      ),
      onChanged: (value) => submitted = value,
    );

    expect(find.byKey(const ValueKey('signature-balance-hero')), findsOneWidget);
    expect(find.byKey(const ValueKey('balance-state-neutral')), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('option-RIGHT_RAW')));
    expect(submitted, 'RIGHT_RAW');
  });

  testWidgets('three-option choice does not opt into binary balance semantics', (
    tester,
  ) async {
    await _pumpQuestion(
      tester,
      question: const DecisionQuestion(
        id: 'three-way',
        prompt: 'Choose one',
        responseType: 'SINGLE_CHOICE',
        options: ['A', 'B', 'C'],
      ),
      onChanged: (_) {},
    );

    expect(find.byKey(const ValueKey('signature-balance-hero')), findsNothing);
    expect(find.byKey(const ValueKey('option-A')), findsOneWidget);
    expect(find.byKey(const ValueKey('option-B')), findsOneWidget);
    expect(find.byKey(const ValueKey('option-C')), findsOneWidget);
  });

  testWidgets('selected side is visual feedback without inventing a percentage', (
    tester,
  ) async {
    await _pumpQuestion(
      tester,
      question: const DecisionQuestion(
        id: 'binary-selected',
        prompt: 'Choose one',
        responseType: 'SINGLE_CHOICE',
        options: ['LEFT_RAW', 'RIGHT_RAW'],
      ),
      value: 'LEFT_RAW',
      onChanged: (_) {},
    );

    expect(find.byKey(const ValueKey('balance-state-leftSelected')), findsOneWidget);
    expect(find.textContaining('%'), findsNothing);
  });

  testWidgets('Reduce Motion collapses hero selection transition to zero', (
    tester,
  ) async {
    await _pumpBalance(
      tester,
      selectedIndex: 1,
      accessibleNavigation: true,
    );

    final animated = tester.widgetList<TweenAnimationBuilder<double>>(
      find.byType(TweenAnimationBuilder<double>),
    );
    expect(animated, isNotEmpty);
    expect(animated.every((widget) => widget.duration == Duration.zero), isTrue);
  });

  testWidgets('hero compacts on a narrow phone and remains semantic', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(280, 700));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await _pumpBalance(tester, selectedIndex: null);

    expect(
      tester.getSize(find.byKey(const ValueKey('signature-balance-hero'))).height,
      122,
    );
    expect(find.bySemanticsLabel(contains('Sol seçenek')), findsOneWidget);
  });

  testWidgets('hero renders in both light and dark themes', (tester) async {
    await _pumpBalance(tester, selectedIndex: 0, themeMode: ThemeMode.light);
    expect(find.byKey(const ValueKey('signature-balance-hero')), findsOneWidget);

    await _pumpBalance(tester, selectedIndex: 1, themeMode: ThemeMode.dark);
    expect(find.byKey(const ValueKey('signature-balance-hero')), findsOneWidget);
  });
}

Future<void> _pumpQuestion(
  WidgetTester tester, {
  required DecisionQuestion question,
  Object? value,
  required ValueChanged<Object> onChanged,
}) async {
  await _pumpLocalized(
    tester,
    child: Scaffold(
      body: SingleChildScrollView(
        child: QuestionInputCard(
          question: question,
          value: value,
          enabled: true,
          onChanged: onChanged,
        ),
      ),
    ),
  );
}

Future<void> _pumpBalance(
  WidgetTester tester, {
  required int? selectedIndex,
  bool accessibleNavigation = false,
  ThemeMode themeMode = ThemeMode.dark,
}) async {
  await _pumpLocalized(
    tester,
    themeMode: themeMode,
    mediaQueryData: MediaQueryData(accessibleNavigation: accessibleNavigation),
    child: Scaffold(
      body: Center(
        child: SizedBox(
          width: 360,
          child: KefeBalanceVisual(
            leftLabel: 'Sol seçenek',
            rightLabel: 'Sağ seçenek',
            selectedIndex: selectedIndex,
          ),
        ),
      ),
    ),
  );
}

Future<void> _pumpLocalized(
  WidgetTester tester, {
  required Widget child,
  ThemeMode themeMode = ThemeMode.dark,
  MediaQueryData? mediaQueryData,
}) async {
  await tester.pumpWidget(
    ProviderScope(
      child: MaterialApp(
        locale: const Locale('tr'),
        theme: KefeTheme.light(),
        darkTheme: KefeTheme.dark(),
        themeMode: themeMode,
        supportedLocales: KefeStrings.supportedLocales,
        localizationsDelegates: const [
          KefeStringsDelegate(),
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        home: mediaQueryData == null
            ? child
            : MediaQuery(data: mediaQueryData, child: child),
      ),
    ),
  );
  await tester.pump();
}
