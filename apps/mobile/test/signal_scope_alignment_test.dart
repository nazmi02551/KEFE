import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/signal/domain/signal_scope_models.dart';
import 'package:kefe_mobile/features/signal/presentation/signal_scope_alignment_card.dart';

void main() {
  group('Signal Scope Alignment Engine (CAP-046)', () {
    test('ADR-0257 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0257-signal-scope-alignment.md');
      final contract = File('../../docs/contracts/signal-scope-alignment.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-SIGNAL-SCOPE-001'));
      expect(contract.readAsStringSync(), contains('STRICTLY_ALIGNED'));
    });

    test('SignalScopeAlignmentReportModel instantiates and round-trips properly', () {
      const dimension = ScopeDimensionModel(
        dimension: 'JURISDICTION',
        declaredScope: 'MUNICIPAL',
        sampleScope: 'Local Constituency (MUNICIPAL)',
        alignmentScore: 0.96,
        isValid: true,
      );

      const model = SignalScopeAlignmentReportModel(
        signalId: '77777777-7777-4777-8777-777777777701',
        caseVersionId: '22222222-2222-4222-8222-222222222222',
        jurisdictionLevel: JurisdictionLevelModel.municipal,
        targetPopulation: 'Kent İçi Raylı Sistem Yolcuları',
        geographicScope: 'İstanbul / Türkiye',
        alignmentStatus: ScopeAlignmentStatusModel.strictlyAligned,
        overallAlignmentScore: 0.92,
        dimensions: [dimension],
        validityWindowDays: 90,
        certifiedAt: '2026-08-20T10:00:00Z',
        scopeSealHash: 'a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890',
      );

      final json = model.toJson();
      final roundTrip = SignalScopeAlignmentReportModel.fromJson(json);

      expect(roundTrip.signalId, model.signalId);
      expect(roundTrip.jurisdictionLevel, JurisdictionLevelModel.municipal);
      expect(roundTrip.alignmentStatus, ScopeAlignmentStatusModel.strictlyAligned);
      expect(roundTrip.overallAlignmentScore, 0.92);
      expect(roundTrip.dimensions.length, 1);
      expect(roundTrip.dimensions.first.isValid, isTrue);
      expect(roundTrip.scopeSealHash, model.scopeSealHash);
    });

    test('InternalAlphaStrings contains signal scope localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.sigScopeEyebrow, contains('SİNYAL KAPSAM UYUMU'));
      expect(tr.sigScopeStAligned, contains('KESİN UYUMLU'));
      expect(tr.sigScopeScoreLabel(92), contains('%92'));
      expect(tr.sigScopeValidityLabel(90), contains('90 Gün'));

      const en = KefeStrings(Locale('en'));
      expect(en.sigScopeEyebrow, contains('SIGNAL SCOPE ALIGNMENT'));
      expect(en.sigScopeStAligned, contains('STRICTLY ALIGNED'));
      expect(en.sigScopeScoreLabel(92), contains('92%'));
      expect(en.sigScopeValidityLabel(90), contains('90 Days'));
    });

    testWidgets('SignalScopeAlignmentCard renders correctly in TR locale', (tester) async {
      const dimension = ScopeDimensionModel(
        dimension: 'JURISDICTION',
        declaredScope: 'MUNICIPAL',
        sampleScope: 'Local Constituency',
        alignmentScore: 0.96,
        isValid: true,
      );

      const model = SignalScopeAlignmentReportModel(
        signalId: '77777777-7777-4777-8777-777777777701',
        caseVersionId: '22222222-2222-4222-8222-222222222222',
        jurisdictionLevel: JurisdictionLevelModel.municipal,
        targetPopulation: 'Kent İçi Raylı Sistem Yolcuları',
        geographicScope: 'İstanbul / Türkiye',
        alignmentStatus: ScopeAlignmentStatusModel.strictlyAligned,
        overallAlignmentScore: 0.92,
        dimensions: [dimension],
        validityWindowDays: 90,
        certifiedAt: '2026-08-20T10:00:00Z',
        scopeSealHash: 'a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890',
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
              child: SignalScopeAlignmentCard(report: model),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(SignalScopeAlignmentCard), findsOneWidget);
      expect(find.text('SİNYAL KAPSAM UYUMU'), findsOneWidget);
      expect(find.text('Sinyal Kapsamı ve Yetki Alanı Uyumu'), findsOneWidget);
      expect(find.text('KESİN UYUMLU'), findsOneWidget);
      expect(find.text('Kapsam Uyumu: %92'), findsOneWidget);
      expect(find.text('Geçerlilik Penceresi: 90 Gün'), findsOneWidget);
      expect(find.text('JURISDICTION'), findsOneWidget);
      expect(find.text('96%'), findsOneWidget);
      expect(find.text('GEÇERLİ SINIR'), findsOneWidget);
    });
  });
}
