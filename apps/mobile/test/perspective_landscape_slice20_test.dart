import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';
import 'package:kefe_mobile/features/decision/presentation/perspective_landscape_visual.dart';

void main() {
  test('Slice 20 contract forbids invented quantitative Perspective position', () {
    final contract =
        jsonDecode(
              File(
                '../../docs/contracts/perspective-landscape-slice20.v1.json',
              ).readAsStringSync(),
            )
            as Map<String, dynamic>;

    expect(contract['contract'], 'perspective-landscape-slice20');
    expect(contract['placement']['post_commit_only'], isTrue);
    expect(contract['placement']['pre_commit_render_forbidden'], isTrue);
    expect(contract['source_truth']['slot_presence_only_for_landscape_geometry'], isTrue);
    expect(contract['source_truth']['local_reranking_forbidden'], isTrue);
    expect(contract['source_truth']['case_id_branch_forbidden'], isTrue);
    expect(
      contract['quantitative_truthfulness']['current_payload_has_user_coordinate'],
      isFalse,
    );
    expect(
      contract['quantitative_truthfulness']['current_payload_has_population_density_coordinate'],
      isFalse,
    );
    expect(
      contract['quantitative_truthfulness']['invented_user_marker_forbidden'],
      isTrue,
    );
    expect(
      contract['quantitative_truthfulness']['invented_user_percentage_forbidden'],
      isTrue,
    );
    expect(
      contract['quantitative_truthfulness']['invented_population_percentage_forbidden'],
      isTrue,
    );
    expect(
      contract['quantitative_truthfulness']['geometry_as_popularity_or_density_forbidden'],
      isTrue,
    );
    expect(contract['presentation']['continuous_animation_forbidden'], isTrue);
    expect(contract['presentation']['live_3d_required'], isFalse);
    expect(contract['invariants']['ideology_inference'], isFalse);
    expect(contract['invariants']['psychometric_inference'], isFalse);
    expect(contract['invariants']['signal_in_scope'], isFalse);
    expect(contract['invariants']['impact_in_scope'], isFalse);
  });

  test('landscape source remains slot-driven and non-quantitative', () {
    final source = File(
      'lib/features/decision/presentation/perspective_landscape_visual.dart',
    ).readAsStringSync();

    expect(source, contains('List<PerspectiveSlot> slots'));
    expect(source, contains('PerspectiveSlot.near'));
    expect(source, contains('PerspectiveSlot.opposing'));
    expect(source, contains('PerspectiveSlot.bridge'));
    expect(source, contains('PerspectiveSlot.alternativeContext'));
    expect(source, isNot(contains('caseId')));
    expect(source, isNot(contains('caseTitle')));
    expect(source, isNot(contains('sampleSize')));
    expect(source, isNot(contains('confidence')));
    expect(source, isNot(contains("'Sen'")));
    expect(source, isNot(contains("'Toplum'")));
    expect(source, isNot(contains("'%'")));
    expect(source, isNot(contains('CircularProgressIndicator')));
  });

  testWidgets('landscape renders only recognized present slots in dark theme', (
    tester,
  ) async {
    await _pumpLandscape(
      tester,
      themeMode: ThemeMode.dark,
      slots: const [
        PerspectiveSlot.near,
        PerspectiveSlot.bridge,
        PerspectiveSlot.opposing,
      ],
    );

    expect(find.byKey(const ValueKey('perspective-landscape')), findsOneWidget);
    expect(
      find.byKey(const ValueKey('perspective-landscape-canvas')),
      findsOneWidget,
    );
    expect(
      find.byKey(const ValueKey('perspective-landscape-slot-near')),
      findsOneWidget,
    );
    expect(
      find.byKey(const ValueKey('perspective-landscape-slot-bridge')),
      findsOneWidget,
    );
    expect(
      find.byKey(const ValueKey('perspective-landscape-slot-opposing')),
      findsOneWidget,
    );
    expect(
      find.byKey(
        const ValueKey('perspective-landscape-slot-alternativeContext'),
      ),
      findsNothing,
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('landscape remains valid in light theme', (tester) async {
    await _pumpLandscape(
      tester,
      themeMode: ThemeMode.light,
      slots: PerspectiveSlot.values,
    );

    expect(find.byKey(const ValueKey('perspective-landscape')), findsOneWidget);
    for (final slot in PerspectiveSlot.values) {
      expect(
        find.byKey(ValueKey('perspective-landscape-slot-${slot.name}')),
        findsOneWidget,
      );
    }
    expect(tester.takeException(), isNull);
  });

  testWidgets('landscape compacts on a constrained phone', (tester) async {
    await tester.binding.setSurfaceSize(const Size(320, 640));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await _pumpLandscape(
      tester,
      themeMode: ThemeMode.dark,
      slots: PerspectiveSlot.values,
    );

    expect(
      tester
          .getSize(find.byKey(const ValueKey('perspective-landscape-canvas')))
          .height,
      176,
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('landscape legend stays usable with enlarged text', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(390, 844));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await _pumpLandscape(
      tester,
      themeMode: ThemeMode.dark,
      slots: PerspectiveSlot.values,
      textScale: 1.6,
    );

    for (final slot in PerspectiveSlot.values) {
      expect(
        find.byKey(ValueKey('perspective-landscape-slot-${slot.name}')),
        findsOneWidget,
      );
    }
    expect(tester.takeException(), isNull);
  });
}

Future<void> _pumpLandscape(
  WidgetTester tester, {
  required ThemeMode themeMode,
  required List<PerspectiveSlot> slots,
  double textScale = 1.0,
}) async {
  await tester.pumpWidget(
    MaterialApp(
      locale: const Locale('tr', 'TR'),
      supportedLocales: KefeStrings.supportedLocales,
      localizationsDelegates: const [
        KefeStringsDelegate(),
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      theme: KefeTheme.light(),
      darkTheme: KefeTheme.dark(),
      themeMode: themeMode,
      builder: (context, child) => MediaQuery(
        data: MediaQuery.of(
          context,
        ).copyWith(textScaler: TextScaler.linear(textScale)),
        child: child!,
      ),
      home: Scaffold(
        body: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: PerspectiveLandscapeVisual(slots: slots),
          ),
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}
