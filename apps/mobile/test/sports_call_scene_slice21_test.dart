import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/product_preview/preview_content_localizer.dart';
import 'package:kefe_mobile/app/product_preview_app.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/localization/kefe_content_localizer.dart';
import 'package:kefe_mobile/core/visual_composition/kefe_visual_composition_flutter.dart';
import 'package:kefe_mobile/core/visual_composition/kefe_visual_composition_models.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/preview_decision_repository.dart';
import 'package:kefe_mobile/features/decision/data/preview_journey_decision_repository.dart';
import 'package:kefe_mobile/features/media_presentation/application/case_media_provider.dart';
import 'package:kefe_mobile/features/media_presentation/data/case_media_repository.dart';
import 'package:kefe_mobile/features/media_presentation/data/preview_case_media_repository.dart';
import 'package:kefe_mobile/features/media_presentation/domain/case_media_models.dart';
import 'package:kefe_mobile/features/media_presentation/presentation/case_media_surface.dart';
import 'package:kefe_mobile/features/media_presentation/presentation/sports_call_scene_visual.dart';

const _sportsCaseId = '11111111-1111-4111-8111-111111111113';
const _sportsCaseVersionId = '22222222-2222-4222-8222-222222222224';
const _dataCaseVersionId = '22222222-2222-4222-8222-222222222223';

void main() {
  test('Slice 21 contract locks illustrative non-evidence boundary', () {
    final contract =
        jsonDecode(
              File(
                '../../docs/contracts/sports-call-scene-slice21.v1.json',
              ).readAsStringSync(),
            )
            as Map<String, dynamic>;

    expect(contract['contract'], 'sports-call-scene-slice21');
    expect(contract['renderer']['code'], 'KEFE_SPORTS_SCENE_V1');
    expect(
      contract['renderer']['selection_source'],
      'CaseMediaRendition.rendererCode',
    );
    expect(contract['renderer']['case_id_branch_forbidden'], isTrue);
    expect(contract['renderer']['case_format_branch_forbidden'], isTrue);
    expect(contract['illustration_truth']['presentation_only'], isTrue);
    expect(contract['illustration_truth']['claim_evidence'], isFalse);
    expect(contract['illustration_truth']['spatial_evidence'], isFalse);
    expect(
      contract['illustration_truth']['geometry_encodes_real_event_coordinates'],
      isFalse,
    );
    expect(
      contract['illustration_truth']['fake_camera_views_forbidden'],
      isTrue,
    );
    expect(contract['illustration_truth']['fake_var_frame_forbidden'], isTrue);
    expect(
      contract['illustration_truth']['fake_offside_line_forbidden'],
      isTrue,
    );
    expect(
      contract['illustration_truth']['evidence_view_tabs_forbidden'],
      isTrue,
    );
    expect(contract['future_spatial_evidence']['in_scope'], isFalse);
    expect(
      contract['future_spatial_evidence']['requires_new_contract'],
      isTrue,
    );
    expect(contract['invariants']['commit_first'], isTrue);
    expect(contract['invariants']['blind_first'], isTrue);
    expect(contract['invariants']['signal_in_scope'], isFalse);
    expect(contract['invariants']['impact_in_scope'], isFalse);
  });

  test(
    'representative Sports CALL copy and answer values remain unchanged',
    () async {
      final repository = PreviewDecisionRepository();
      final item = await repository.fetchCase(_sportsCaseId);

      expect(item.versionId, _sportsCaseVersionId);
      expect(item.format, 'SPORTS_CALL');
      expect(item.domain, 'SPORTS');
      expect(item.title, 'Bu pozisyonda penaltı kararı doğru muydu?');
      expect(
        item.summary,
        'Temas, avantaj ve VAR müdahalesi üzerinden bir Sports CALL yap.',
      );
      expect(
        item.questions.first.prompt,
        'Hakemin penaltı kararını nasıl değerlendiriyorsun?',
      );
      expect(item.questions.first.responseType, 'SINGLE_CHOICE');
      expect(item.questions.first.options, const ['Doğru', 'Yanlış']);
      expect(item.questions[1].responseType, 'CONFIDENCE');
    },
  );

  test(
    'Preview media selects Sports renderer without changing other assets',
    () async {
      const repository = PreviewCaseMediaRepository();

      final sports = await repository.fetchForCaseVersion(
        _sportsCaseVersionId,
        slot: CaseMediaSlot.caseHero,
        postCommitAvailable: false,
      );
      final data = await repository.fetchForCaseVersion(
        _dataCaseVersionId,
        slot: CaseMediaSlot.caseHero,
        postCommitAvailable: false,
      );

      expect(sports, hasLength(1));
      expect(sports.single.rendition.rendererCode, 'KEFE_SPORTS_SCENE_V1');
      expect(sports.single.rendition.locator, 'SPORTS_DECISION');
      expect(sports.single.exposurePhase, MediaExposurePhase.preCommitSafe);
      expect(
        sports.single.altText,
        'Futbol sahası, top ve karar anını temsil eden soyut KEFE illüstrasyonu.',
      );
      expect(
        sports.single.attribution,
        'KEFE Product Preview · temsili illüstrasyon',
      );

      expect(data, hasLength(1));
      expect(data.single.rendition.rendererCode, 'KEFE_ABSTRACT_V1');
      expect(data.single.rendition.locator, 'DATA_NETWORK');
    },
  );

  test(
    'scene renderer source contains no fake evidence controls or Case branching',
    () {
      final source = File(
        'lib/features/media_presentation/presentation/sports_call_scene_visual.dart',
      ).readAsStringSync();
      final surfaceSource = File(
        'lib/features/media_presentation/presentation/case_media_surface.dart',
      ).readAsStringSync();

      expect(source, isNot(contains('caseId')));
      expect(source, isNot(contains('caseTitle')));
      expect(source, isNot(contains('SPORTS_CALL')));
      expect(source, isNot(contains('VAR')));
      expect(source, isNot(contains('Üstten')));
      expect(source, isNot(contains('Hakem')));
      expect(source, isNot(contains('offside')));
      expect(source, isNot(contains('TabBar')));
      expect(source, isNot(contains('IconButton')));
      expect(source, isNot(contains('GestureDetector')));
      expect(source, isNot(contains('InkWell')));
      expect(surfaceSource, contains("'KEFE_SPORTS_SCENE_V1'"));
      expect(
        surfaceSource,
        isNot(contains("item.caseVersionId == '$_sportsCaseVersionId'")),
      );
    },
  );

  testWidgets('Sports renderer is theme-adaptive and text-scale safe', (
    tester,
  ) async {
    await _pumpMediaSurface(tester, themeMode: ThemeMode.dark, textScale: 1.0);

    expect(find.byType(SportsCallSceneVisual), findsOneWidget);
    expect(
      find.byKey(const ValueKey('case-media-CASE_HERO-$_sportsCaseVersionId')),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);

    await _pumpMediaSurface(tester, themeMode: ThemeMode.light, textScale: 1.6);
    expect(find.byType(SportsCallSceneVisual), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'unsupported renderer falls back without blocking media surface',
    (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            caseMediaRepositoryProvider.overrideWithValue(
              const _UnsupportedRendererRepository(),
            ),
          ],
          child: MaterialApp(
            theme: KefeTheme.light(),
            home: const Scaffold(
              body: CaseMediaSurface(
                caseVersionId: 'fallback-case-version',
                slot: CaseMediaSlot.caseHero,
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byType(KefeVisualCompositionPlaceholder), findsOneWidget);
      expect(find.byType(SportsCallSceneVisual), findsNothing);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'Product Preview reaches Sports scene before Commit without Reveal',
    (tester) async {
      tester.platformDispatcher.localeTestValue = const Locale('tr', 'TR');
      addTearDown(tester.platformDispatcher.clearLocaleTestValue);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            decisionRepositoryProvider.overrideWithValue(
              PreviewJourneyDecisionRepository(),
            ),
            kefeContentLocalizerProvider.overrideWithValue(
              const PreviewContentLocalizer(),
            ),
            caseMediaRepositoryProvider.overrideWithValue(
              const PreviewCaseMediaRepository(),
            ),
          ],
          child: const ProductPreviewApp(),
        ),
      );
      await tester.pumpAndSettle();

      final sportsTitle = find.text(
        'Bu pozisyonda penaltı kararı doğru muydu?',
      );
      final sportsCard = find.byKey(
        const ValueKey('explore-case-$_sportsCaseId'),
      );
      await tester.scrollUntilVisible(
        sportsCard,
        280,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.pump();
      expect(sportsCard, findsOneWidget);
      expect(sportsTitle, findsOneWidget);
      await tester.tap(sportsCard);
      await _pumpUntilFound(tester, find.byType(SportsCallSceneVisual));

      expect(find.byType(SportsCallSceneVisual), findsOneWidget);
      expect(
        find.byKey(
          const ValueKey('case-media-CASE_HERO-$_sportsCaseVersionId'),
        ),
        findsOneWidget,
      );
      expect(
        find.text('Hakemin penaltı kararını nasıl değerlendiriyorsun?'),
        findsOneWidget,
      );
      expect(find.byKey(const ValueKey('option-Doğru')), findsOneWidget);
      expect(find.byKey(const ValueKey('option-Yanlış')), findsOneWidget);
      expect(find.byKey(const ValueKey('reveal-card')), findsNothing);
    },
  );
}

Future<void> _pumpUntilFound(WidgetTester tester, Finder finder) async {
  for (var attempt = 0; attempt < 20; attempt++) {
    await tester.pump(const Duration(milliseconds: 100));
    if (finder.evaluate().isNotEmpty) return;
  }
}

Future<void> _pumpMediaSurface(
  WidgetTester tester, {
  required ThemeMode themeMode,
  required double textScale,
}) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        caseMediaRepositoryProvider.overrideWithValue(
          const PreviewCaseMediaRepository(),
        ),
      ],
      child: MaterialApp(
        theme: KefeTheme.light(),
        darkTheme: KefeTheme.dark(),
        themeMode: themeMode,
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(
            context,
          ).copyWith(textScaler: TextScaler.linear(textScale)),
          child: child!,
        ),
        home: const Scaffold(
          body: Padding(
            padding: EdgeInsets.all(16),
            child: CaseMediaSurface(
              caseVersionId: _sportsCaseVersionId,
              slot: CaseMediaSlot.caseHero,
            ),
          ),
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

class _UnsupportedRendererRepository implements CaseMediaRepository {
  const _UnsupportedRendererRepository();

  @override
  Future<List<CaseMediaPresentation>> fetchForCaseVersion(
    String caseVersionId, {
    required CaseMediaSlot slot,
    required bool postCommitAvailable,
  }) async => [
    CaseMediaPresentation(
      id: 'fallback-media',
      caseVersionId: caseVersionId,
      slot: slot,
      kind: CaseMediaKind.illustration,
      assetIdentity: 'test:fallback',
      assetContentHash: 'fallback-hash',
      altText: 'Fallback test illustration',
      exposurePhase: MediaExposurePhase.preCommitSafe,
      rendition: const CaseMediaRendition(
        rendererCode: 'UNSUPPORTED_RENDERER',
        locator: 'NONE',
        aspectRatio: 1.85,
        composition: KefeVisualCompositionPolicy(
          fallback: KefeVisualFallbackPolicy.semanticPlaceholder,
        ),
      ),
    ),
  ];
}
