import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/visual_composition/kefe_visual_composition_models.dart';
import 'package:kefe_mobile/features/media_presentation/application/case_media_provider.dart';
import 'package:kefe_mobile/features/media_presentation/data/case_media_repository.dart';
import 'package:kefe_mobile/features/media_presentation/data/preview_case_media_repository.dart';
import 'package:kefe_mobile/features/media_presentation/domain/case_media_models.dart';
import 'package:kefe_mobile/features/media_presentation/presentation/case_media_surface.dart';

void main() {
  group('Slice 17 contract and policy', () {
    test('executable contract keeps visual work inside the locked boundary', () {
      final contract =
          jsonDecode(
                File(
                  '../../docs/contracts/high-fidelity-visual-foundation-slice17.v1.json',
                ).readAsStringSync(),
              )
              as Map<String, dynamic>;

      expect(contract['contract'], 'high-fidelity-visual-foundation-slice17');
      expect(contract['scope']['visual_composition_foundation'], isTrue);
      expect(
        contract['scope']['screen_specific_high_fidelity_convergence'],
        isFalse,
      );
      expect(contract['scope']['product_semantics_change'], isFalse);
      expect(contract['architecture']['case_agnostic_composition'], isTrue);
      expect(contract['architecture']['webview_required'], isFalse);
      expect(contract['architecture']['threejs_required'], isFalse);
      expect(
        contract['presentation_contract']['focal_crop_policy_required'],
        isTrue,
      );
      expect(
        contract['presentation_contract']['safe_area_policy_required'],
        isTrue,
      );
      expect(
        contract['presentation_contract']['fallback_policy_required'],
        isTrue,
      );
      expect(contract['performance']['low_end_android_first_class'], isTrue);
    });

    test('shared composition policies are bounded and reusable', () {
      const hero = KefeVisualCompositionPolicy.hero;
      const card = KefeVisualCompositionPolicy.card;

      expect(hero.themeSuitability, KefeVisualThemeSuitability.adaptive);
      expect(hero.fallback, KefeVisualFallbackPolicy.semanticPlaceholder);
      expect(hero.motion, KefeVisualMotionPolicy.reducedMotionAware);
      expect(hero.performance.cacheClass, KefeVisualCacheClass.hero);
      expect(hero.performance.maxDecodeWidthPx, lessThanOrEqualTo(1600));
      expect(hero.performance.maxDecodeHeightPx, lessThanOrEqualTo(1200));
      expect(
        hero.performance.maxDecodedBytes,
        lessThanOrEqualTo(8 * 1024 * 1024),
      );

      expect(card.fallback, KefeVisualFallbackPolicy.textHierarchyOnly);
      expect(card.performance.cacheClass, KefeVisualCacheClass.compact);
      expect(card.safeArea.left, greaterThan(0));
      expect(card.safeArea.right, greaterThan(0));
    });

    test(
      'preview renditions pin identity, hash, focal policy and budget',
      () async {
        const repository = PreviewCaseMediaRepository();
        final items = await repository.fetchForCaseVersion(
          '22222222-2222-4222-8222-222222222222',
          slot: CaseMediaSlot.caseHero,
          postCommitAvailable: false,
        );

        expect(items, hasLength(1));
        final item = items.single;
        final policy = item.rendition.composition;
        expect(item.assetIdentity, startsWith('preview-abstract:'));
        expect(item.assetContentHash, matches(RegExp(r'^[a-f0-9]{64}$')));
        expect(item.exposurePhase, MediaExposurePhase.preCommitSafe);
        expect(policy.focalPoint.x, inInclusiveRange(0, 1));
        expect(policy.focalPoint.y, inInclusiveRange(0, 1));
        expect(policy.safeArea.left, greaterThan(0));
        expect(policy.themeSuitability, KefeVisualThemeSuitability.adaptive);
        expect(
          policy.performance.maxDecodedBytes,
          lessThanOrEqualTo(8 * 1024 * 1024),
        );
      },
    );
  });

  group('Slice 17 deterministic visual states', () {
    testWidgets('loading becomes an explicit non-animated placeholder', (
      tester,
    ) async {
      final completer = Completer<List<CaseMediaPresentation>>();
      await _pumpSurface(tester, _CompleterMediaRepository(completer));

      expect(
        find.byKey(
          const ValueKey(
            'case-media-loading-CASE_HERO-case-version-under-test',
          ),
        ),
        findsOneWidget,
      );
      expect(find.byType(CircularProgressIndicator), findsNothing);

      completer.complete(const []);
      await tester.pumpAndSettle();
      expect(
        find.byKey(
          const ValueKey('case-media-empty-CASE_HERO-case-version-under-test'),
        ),
        findsOneWidget,
      );
    });

    testWidgets('post-Commit-only media stays blocked before Commit', (
      tester,
    ) async {
      final item = _media(
        exposurePhase: MediaExposurePhase.postCommitOnly,
        policy: KefeVisualCompositionPolicy.hero,
      );
      await _pumpSurface(tester, _StaticMediaRepository([item]));
      await tester.pumpAndSettle();

      expect(
        find.byKey(
          const ValueKey(
            'case-media-exposure-blocked-CASE_HERO-case-version-under-test',
          ),
        ),
        findsOneWidget,
      );
      expect(
        find.byKey(
          const ValueKey('case-media-CASE_HERO-case-version-under-test'),
        ),
        findsNothing,
      );
    });

    testWidgets('unsupported renderer degrades without blocking the task', (
      tester,
    ) async {
      final item = _media(
        rendererCode: 'FUTURE_PROVIDER_NEUTRAL_RENDERER',
        policy: KefeVisualCompositionPolicy.hero,
      );
      await _pumpSurface(tester, _StaticMediaRepository([item]));
      await tester.pumpAndSettle();

      expect(
        find.byKey(
          const ValueKey(
            'case-media-fallback-renderer-CASE_HERO-case-version-under-test',
          ),
        ),
        findsOneWidget,
      );
      expect(find.byType(CircularProgressIndicator), findsNothing);
    });

    testWidgets('theme-incompatible rendition follows explicit fallback', (
      tester,
    ) async {
      final item = _media(
        policy: const KefeVisualCompositionPolicy(
          themeSuitability: KefeVisualThemeSuitability.darkOnly,
          fallback: KefeVisualFallbackPolicy.semanticPlaceholder,
          performance: KefeVisualPerformanceBudget.hero,
        ),
      );
      await _pumpSurface(
        tester,
        _StaticMediaRepository([item]),
        themeMode: ThemeMode.light,
      );
      await tester.pumpAndSettle();

      expect(
        find.byKey(
          const ValueKey(
            'case-media-fallback-theme-CASE_HERO-case-version-under-test',
          ),
        ),
        findsOneWidget,
      );
    });

    testWidgets('supported renderer remains theme-adaptive and semantic', (
      tester,
    ) async {
      final item = _media(policy: KefeVisualCompositionPolicy.hero);
      await _pumpSurface(
        tester,
        _StaticMediaRepository([item]),
        themeMode: ThemeMode.dark,
      );
      await tester.pumpAndSettle();

      expect(
        find.byKey(
          const ValueKey('case-media-CASE_HERO-case-version-under-test'),
        ),
        findsOneWidget,
      );
      expect(find.bySemanticsLabel('Temsili KEFE görseli'), findsOneWidget);
    });
  });
}

Future<void> _pumpSurface(
  WidgetTester tester,
  CaseMediaRepository repository, {
  ThemeMode themeMode = ThemeMode.dark,
}) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [caseMediaRepositoryProvider.overrideWithValue(repository)],
      child: MaterialApp(
        theme: KefeTheme.light(),
        darkTheme: KefeTheme.dark(),
        themeMode: themeMode,
        home: const Scaffold(
          body: Center(
            child: SizedBox(
              width: 360,
              child: CaseMediaSurface(
                caseVersionId: 'case-version-under-test',
                slot: CaseMediaSlot.caseHero,
              ),
            ),
          ),
        ),
      ),
    ),
  );
  await tester.pump();
}

CaseMediaPresentation _media({
  String rendererCode = 'KEFE_ABSTRACT_V1',
  MediaExposurePhase exposurePhase = MediaExposurePhase.preCommitSafe,
  required KefeVisualCompositionPolicy policy,
}) {
  return CaseMediaPresentation(
    id: 'media-under-test',
    caseVersionId: 'case-version-under-test',
    slot: CaseMediaSlot.caseHero,
    kind: CaseMediaKind.illustration,
    assetIdentity: 'test:asset',
    assetContentHash:
        'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    altText: 'Temsili KEFE görseli',
    exposurePhase: exposurePhase,
    rendition: CaseMediaRendition(
      rendererCode: rendererCode,
      locator: 'RESOURCE_PRIORITY',
      aspectRatio: 1.85,
      composition: policy,
    ),
  );
}

class _StaticMediaRepository implements CaseMediaRepository {
  const _StaticMediaRepository(this.items);

  final List<CaseMediaPresentation> items;

  @override
  Future<List<CaseMediaPresentation>> fetchForCaseVersion(
    String caseVersionId, {
    required CaseMediaSlot slot,
    required bool postCommitAvailable,
  }) async => items;
}

class _CompleterMediaRepository implements CaseMediaRepository {
  const _CompleterMediaRepository(this.completer);

  final Completer<List<CaseMediaPresentation>> completer;

  @override
  Future<List<CaseMediaPresentation>> fetchForCaseVersion(
    String caseVersionId, {
    required CaseMediaSlot slot,
    required bool postCommitAvailable,
  }) => completer.future;
}
