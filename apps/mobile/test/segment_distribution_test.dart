import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/segment_distribution_models.dart';
import 'package:kefe_mobile/features/decision/presentation/segment_distribution_card.dart';

void main() {
  group('Privacy-Safe Segment Distribution Engine (CAP-036)', () {
    test('ADR-0252 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0252-privacy-safe-segment-distribution.md');
      final contract = File('../../docs/contracts/segment-distribution.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-SEGMENT-DISTRIBUTION-001'));
      expect(contract.readAsStringSync(), contains('minimum_sample_threshold'));
    });

    test('SegmentDistributionModel instantiates and round-trips correctly', () {
      const model = SegmentDistributionModel(
        caseVersionId: 'case-ver-seg-1',
        minimumSampleThreshold: 30,
        overallSampleSize: 520,
        segments: [
          SegmentCohortModel(
            cohortType: 'AGE_COHORT',
            cohortLabel: 'Genç Yetişkin (18-29)',
            sampleSize: 140,
            isSuppressed: false,
            optionShares: {'A': 0.6, 'B': 0.4},
            primaryChoice: 'A',
            entropyScore: 0.97,
          ),
          SegmentCohortModel(
            cohortType: 'EXPERIENCE_LEVEL',
            cohortLabel: 'Küçük Grup',
            sampleSize: 12,
            isSuppressed: true,
            suppressionReason: 'INSUFFICIENT_SAMPLE_PRIVACY_THRESHOLD',
            optionShares: {},
            primaryChoice: null,
            entropyScore: 0.0,
          ),
        ],
        privacyGuarantees: PrivacyGuaranteesModel(
          kAnonymityThreshold: 30,
          noIndividualProfiling: true,
          differentialPrivacyNoiseApplied: true,
        ),
        generatedAt: '2026-09-04T10:00:00Z',
      );

      expect(model.caseVersionId, 'case-ver-seg-1');
      expect(model.minimumSampleThreshold, 30);
      expect(model.overallSampleSize, 520);
      expect(model.segments.length, 2);
      expect(model.segments.first.isSuppressed, isFalse);
      expect(model.segments.last.isSuppressed, isTrue);

      final json = model.toJson();
      final roundTrip = SegmentDistributionModel.fromJson(json);
      expect(roundTrip.caseVersionId, model.caseVersionId);
      expect(roundTrip.minimumSampleThreshold, 30);
      expect(roundTrip.segments.first.primaryChoice, 'A');
      expect(roundTrip.segments.last.suppressionReason, 'INSUFFICIENT_SAMPLE_PRIVACY_THRESHOLD');
      expect(roundTrip.privacyGuarantees.noIndividualProfiling, isTrue);
    });

    test('InternalAlphaStrings contains Segment Distribution localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.segmentDistEyebrow, contains('GİZLİLİK KORUMALI'));
      expect(tr.segmentDistTitle, contains('Toplumsal Kesim'));
      expect(tr.segmentDistPrivacyBadge(30), contains('k >= 30'));

      const en = KefeStrings(Locale('en'));
      expect(en.segmentDistEyebrow, contains('PRIVACY-SAFE'));
      expect(en.segmentDistTitle, contains('Cohort Perspective'));
      expect(en.segmentDistPrivacyBadge(30), contains('k >= 30'));
    });

    testWidgets('SegmentDistributionCard renders properly in TR locale', (tester) async {
      const model = SegmentDistributionModel(
        caseVersionId: 'case-test-1',
        minimumSampleThreshold: 30,
        overallSampleSize: 600,
        segments: [
          SegmentCohortModel(
            cohortType: 'AGE_COHORT',
            cohortLabel: 'Orta Yaş (30-49)',
            sampleSize: 250,
            isSuppressed: false,
            optionShares: {'A': 0.55, 'B': 0.45},
            primaryChoice: 'A',
            entropyScore: 0.99,
          ),
          SegmentCohortModel(
            cohortType: 'EXPERIENCE_LEVEL',
            cohortLabel: 'Yeni Katılımcı',
            sampleSize: 18,
            isSuppressed: true,
            suppressionReason: 'INSUFFICIENT_SAMPLE_PRIVACY_THRESHOLD',
            optionShares: {},
            primaryChoice: null,
            entropyScore: 0.0,
          ),
        ],
        privacyGuarantees: PrivacyGuaranteesModel(
          kAnonymityThreshold: 30,
          noIndividualProfiling: true,
          differentialPrivacyNoiseApplied: true,
        ),
        generatedAt: '2026-09-04T10:00:00Z',
      );

      await tester.pumpWidget(
        MaterialApp(
          theme: ThemeData.dark().copyWith(
            extensions: const [KefeVisualTheme.dark],
          ),
          locale: const Locale('tr', 'TR'),
          supportedLocales: KefeStrings.supportedLocales,
          localizationsDelegates: const [
            KefeStringsDelegate(),
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          home: const Scaffold(
            body: SingleChildScrollView(
              child: SegmentDistributionCard(
                distribution: model,
              ),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(SegmentDistributionCard), findsOneWidget);
      expect(find.textContaining('GİZLİLİK KORUMALI'), findsOneWidget);
      expect(find.textContaining('Toplumsal Kesim'), findsOneWidget);
      expect(find.textContaining('k >= 30'), findsOneWidget);
      expect(find.text('Orta Yaş (30-49)'), findsOneWidget);
      expect(find.text('Yeni Katılımcı'), findsOneWidget);
      expect(find.byIcon(Icons.lock_outline_rounded), findsOneWidget);
      expect(find.textContaining('Anonimliği korumak için gizlendi'), findsOneWidget);
    });
  });
}
