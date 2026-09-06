import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/impact/domain/signal_target_models.dart';
import 'package:kefe_mobile/features/impact/presentation/signal_target_registry_card.dart';

void main() {
  group('Signal Target Registry Engine (CAP-048)', () {
    test('ADR-0259 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0259-signal-target-registry.md');
      final contract = File('../../docs/contracts/signal-target-registry.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-IMPACT-TARGET-001'));
      expect(contract.readAsStringSync(), contains('DESIGNATED_INSTITUTIONAL_TARGET'));
    });

    test('SignalTargetRegistryReportModel instantiates and round-trips properly', () {
      const primaryTarget = SignalTargetItemModel(
        targetId: 'bbbbbbbb-1111-4bbb-8bbb-111111111111',
        targetName: 'İstanbul Büyükşehir Belediyesi UKOME',
        targetType: TargetTypeModel.municipalGovernment,
        jurisdictionLevel: 'MUNICIPAL',
        officialContactChannel: 'ukome@ibb.gov.tr',
        dispatchStatus: DispatchStatusModel.acknowledged,
        responseDueDays: 30,
        dispatchedAt: '2026-08-16T09:00:00Z',
        acknowledgedAt: '2026-08-18T14:20:00Z',
      );

      const model = SignalTargetRegistryReportModel(
        signalId: '77777777-7777-4777-8777-777777777701',
        caseVersionId: '22222222-2222-4222-8222-222222222222',
        primaryTargetId: 'bbbbbbbb-1111-4bbb-8bbb-111111111111',
        targets: [primaryTarget],
        certifiedAt: '2026-08-20T10:00:00Z',
        registryProofHash: '1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
      );

      final json = model.toJson();
      final roundTrip = SignalTargetRegistryReportModel.fromJson(json);

      expect(roundTrip.signalId, model.signalId);
      expect(roundTrip.primaryTargetId, model.primaryTargetId);
      expect(roundTrip.targets.length, 1);
      expect(roundTrip.targets.first.targetType, TargetTypeModel.municipalGovernment);
      expect(roundTrip.targets.first.dispatchStatus, DispatchStatusModel.acknowledged);
      expect(roundTrip.registryProofHash, model.registryProofHash);
    });

    test('InternalAlphaStrings contains signal target localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.sigTargetEyebrow, contains('SİNYAL HEDEF KAYIT DEFTERİ'));
      expect(tr.sigTargetPrimaryBadge, contains('BİRİNCİL HEDEF'));
      expect(tr.sigTargetStAcknowledged, contains('RESMİ ALINDI ONAYI'));
      expect(tr.sigTargetResponseDue(30), contains('30 Gün'));

      const en = KefeStrings(Locale('en'));
      expect(en.sigTargetEyebrow, contains('SIGNAL TARGET REGISTRY'));
      expect(en.sigTargetPrimaryBadge, contains('PRIMARY TARGET'));
      expect(en.sigTargetStAcknowledged, contains('OFFICIALLY ACKNOWLEDGED'));
      expect(en.sigTargetResponseDue(30), contains('30 Days'));
    });

    testWidgets('SignalTargetRegistryCard renders correctly in TR locale', (tester) async {
      const primaryTarget = SignalTargetItemModel(
        targetId: 'bbbbbbbb-1111-4bbb-8bbb-111111111111',
        targetName: 'İstanbul Büyükşehir Belediyesi UKOME',
        targetType: TargetTypeModel.municipalGovernment,
        jurisdictionLevel: 'MUNICIPAL',
        officialContactChannel: 'ukome@ibb.gov.tr',
        dispatchStatus: DispatchStatusModel.acknowledged,
        responseDueDays: 30,
        dispatchedAt: '2026-08-16T09:00:00Z',
        acknowledgedAt: '2026-08-18T14:20:00Z',
      );

      const model = SignalTargetRegistryReportModel(
        signalId: '77777777-7777-4777-8777-777777777701',
        caseVersionId: '22222222-2222-4222-8222-222222222222',
        primaryTargetId: 'bbbbbbbb-1111-4bbb-8bbb-111111111111',
        targets: [primaryTarget],
        certifiedAt: '2026-08-20T10:00:00Z',
        registryProofHash: '1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
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
              child: SignalTargetRegistryCard(report: model),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(SignalTargetRegistryCard), findsOneWidget);
      expect(find.text('SİNYAL HEDEF KAYIT DEFTERİ'), findsOneWidget);
      expect(find.text('Kurumsal ve Düzenleyici Hedef Merciler'), findsOneWidget);
      expect(find.text('1 Targets Registered'), findsOneWidget);
      expect(find.text('İstanbul Büyükşehir Belediyesi UKOME'), findsOneWidget);
      expect(find.text('RESMİ ALINDI ONAYI'), findsOneWidget);
      expect(find.text('Cevap Süresi: 30 Gün'), findsOneWidget);
      expect(find.text('İletişim Kanalı: ukome@ibb.gov.tr'), findsOneWidget);
    });
  });
}
