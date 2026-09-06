import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/signal/domain/signal_versioning_models.dart';
import 'package:kefe_mobile/features/signal/presentation/signal_versioning_card.dart';

void main() {
  group('Signal Versioning & Audit Chain Engine (CAP-047)', () {
    test('ADR-0258 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0258-signal-versioning.md');
      final contract = File('../../docs/contracts/signal-versioning.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-SIGNAL-VERSIONING-001'));
      expect(contract.readAsStringSync(), contains('METHODOLOGY_VERSION_PINNING'));
    });

    test('SignalVersioningReportModel instantiates and round-trips properly', () {
      const s1 = SignalSnapshotModel(
        snapshotId: 'aaaaaaaa-1111-4aaa-8aaa-111111111111',
        methodologyVersion: 'v1.0.0',
        methodologyName: 'Baseline Tri-Axial Proportion',
        sampleSize: 850,
        confidenceScore: 0.88,
        consensusDistribution: {'YES': 0.72, 'NO': 0.28},
        calculatedAt: '2026-08-01T10:00:00Z',
        parentSnapshotHash: null,
        snapshotHash: '1111111111111111111111111111111111111111111111111111111111111111',
      );

      const s2 = SignalSnapshotModel(
        snapshotId: 'aaaaaaaa-2222-4aaa-8aaa-222222222222',
        methodologyVersion: 'v1.2.0-entropy',
        methodologyName: 'Entropy-Weighted Sybil-Shielded Consensus',
        sampleSize: 1420,
        confidenceScore: 0.94,
        consensusDistribution: {'YES': 0.70, 'NO': 0.30},
        calculatedAt: '2026-08-15T14:30:00Z',
        parentSnapshotHash: '1111111111111111111111111111111111111111111111111111111111111111',
        snapshotHash: '2222222222222222222222222222222222222222222222222222222222222222',
      );

      const delta = MethodologyDeltaModel(
        fromVersion: 'v1.0.0',
        toVersion: 'v1.2.0-entropy',
        distributionShift: 0.02,
        confidenceDelta: 0.06,
        notes: 'Entropy weighting applied without mutating baseline v1.0.0 snapshot.',
      );

      const model = SignalVersioningReportModel(
        signalId: '77777777-7777-4777-8777-777777777701',
        caseVersionId: '22222222-2222-4222-8222-222222222222',
        currentVersion: 'v1.2.0-entropy',
        currentMethodologyHash: '2222222222222222222222222222222222222222222222222222222222222222',
        snapshots: [s1, s2],
        latestDelta: delta,
        auditChainValid: true,
        certifiedAt: '2026-08-20T12:00:00Z',
      );

      final json = model.toJson();
      final roundTrip = SignalVersioningReportModel.fromJson(json);

      expect(roundTrip.signalId, model.signalId);
      expect(roundTrip.currentVersion, 'v1.2.0-entropy');
      expect(roundTrip.auditChainValid, isTrue);
      expect(roundTrip.snapshots.length, 2);
      expect(roundTrip.snapshots[1].parentSnapshotHash, roundTrip.snapshots[0].snapshotHash);
      expect(roundTrip.latestDelta?.distributionShift, 0.02);
    });

    test('InternalAlphaStrings contains signal versioning localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.sigVersEyebrow, contains('SİNYAL SÜRÜMLENDİRME'));
      expect(tr.sigVersChainVerified, contains('ZİNCİR BÜTÜNLÜĞÜ DOĞRULANDI'));
      expect(tr.sigVersCurrentVersionLabel('v1.2.0'), contains('Aktif: v1.2.0'));
      expect(tr.sigVersDeltaShiftLabel(2), contains('%2'));

      const en = KefeStrings(Locale('en'));
      expect(en.sigVersEyebrow, contains('SIGNAL VERSIONING'));
      expect(en.sigVersChainVerified, contains('CHAIN INTEGRITY VERIFIED'));
      expect(en.sigVersCurrentVersionLabel('v1.2.0'), contains('Active: v1.2.0'));
      expect(en.sigVersDeltaShiftLabel(2), contains('2%'));
    });

    testWidgets('SignalVersioningCard renders correctly in TR locale', (tester) async {
      const s1 = SignalSnapshotModel(
        snapshotId: 'aaaaaaaa-1111-4aaa-8aaa-111111111111',
        methodologyVersion: 'v1.0.0',
        methodologyName: 'Baseline Tri-Axial Proportion',
        sampleSize: 850,
        confidenceScore: 0.88,
        consensusDistribution: {'YES': 0.72, 'NO': 0.28},
        calculatedAt: '2026-08-01T10:00:00Z',
        parentSnapshotHash: null,
        snapshotHash: '1111111111111111111111111111111111111111111111111111111111111111',
      );

      const s2 = SignalSnapshotModel(
        snapshotId: 'aaaaaaaa-2222-4aaa-8aaa-222222222222',
        methodologyVersion: 'v1.2.0-entropy',
        methodologyName: 'Entropy-Weighted Sybil-Shielded Consensus',
        sampleSize: 1420,
        confidenceScore: 0.94,
        consensusDistribution: {'YES': 0.70, 'NO': 0.30},
        calculatedAt: '2026-08-15T14:30:00Z',
        parentSnapshotHash: '1111111111111111111111111111111111111111111111111111111111111111',
        snapshotHash: '2222222222222222222222222222222222222222222222222222222222222222',
      );

      const delta = MethodologyDeltaModel(
        fromVersion: 'v1.0.0',
        toVersion: 'v1.2.0-entropy',
        distributionShift: 0.02,
        confidenceDelta: 0.06,
        notes: 'Entropy weighting applied without mutating baseline v1.0.0 snapshot.',
      );

      const model = SignalVersioningReportModel(
        signalId: '77777777-7777-4777-8777-777777777701',
        caseVersionId: '22222222-2222-4222-8222-222222222222',
        currentVersion: 'v1.2.0-entropy',
        currentMethodologyHash: '2222222222222222222222222222222222222222222222222222222222222222',
        snapshots: [s1, s2],
        latestDelta: delta,
        auditChainValid: true,
        certifiedAt: '2026-08-20T12:00:00Z',
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
              child: SignalVersioningCard(report: model),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(SignalVersioningCard), findsOneWidget);
      expect(find.text('SİNYAL SÜRÜMLENDİRME VE DENETİM ZİNCİRİ'), findsOneWidget);
      expect(find.text('Metodoloji Sürümüne Bağlı Sinyal Geçmişi'), findsOneWidget);
      expect(find.text('Aktif: v1.2.0-entropy'), findsOneWidget);
      expect(find.text('ZİNCİR BÜTÜNLÜĞÜ DOĞRULANDI'), findsOneWidget);
      expect(find.text('2 Snapshots'), findsOneWidget);
      expect(find.text('Metodoloji Güncelleme Farkı'), findsOneWidget);
      expect(find.text('v1.0.0 -> v1.2.0-entropy'), findsOneWidget);
      expect(find.text('Dağılım Farkı: %2'), findsOneWidget);
      expect(find.text('Güvenilirlik Artışı: +%6'), findsOneWidget);
      expect(find.text('Baseline Tri-Axial Proportion'), findsOneWidget);
      expect(find.text('Entropy-Weighted Sybil-Shielded Consensus'), findsOneWidget);
    });
  });
}
