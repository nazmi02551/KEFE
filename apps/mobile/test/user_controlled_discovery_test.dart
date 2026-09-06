import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/explore/domain/user_discovery_profile_models.dart';
import 'package:kefe_mobile/features/explore/presentation/user_discovery_profile_sheet.dart';

void main() {
  group('User-Controlled Discovery Profile (CAP-077)', () {
    test('ADR-0247 and contract exist and are valid', () {
      final adr = File(
        '../../docs/adr/0247-user-controlled-discovery-profile.md',
      );
      final contract = File(
        '../../docs/contracts/user-controlled-discovery.v1.json',
      );

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(
        contract.readAsStringSync(),
        contains('KEFE-USER-DISCOVERY-001'),
      );
      expect(contract.readAsStringSync(), contains('NO_ENGAGEMENT_MAXIMIZATION'));
      expect(contract.readAsStringSync(), contains('CIVIC'));
    });

    test('UserDiscoveryProfileModel instantiates and updates with copyWith', () {
      final profile = UserDiscoveryProfileModel(
        userId: 'actor-123',
        preferredDomains: const [
          DomainPreferenceModel.civic,
          DomainPreferenceModel.technology,
        ],
        complexityLevel: ComplexityLevelModel.balanced,
        freshnessPreference: FreshnessPreferenceModel.balanced,
        realEventPreference: RealEventPreferenceModel.balanced,
        diversificationBoost: 0.5,
        updatedAt: DateTime.utc(2026, 8, 30),
      );

      expect(profile.userId, 'actor-123');
      expect(profile.preferredDomains.length, 2);
      expect(profile.diversificationBoost, 0.5);

      final updated = profile.copyWith(
        complexityLevel: ComplexityLevelModel.deepDeliberation,
        diversificationBoost: 0.8,
      );

      expect(updated.complexityLevel, ComplexityLevelModel.deepDeliberation);
      expect(updated.diversificationBoost, 0.8);
      expect(updated.userId, 'actor-123');
    });

    test('UserDiscoveryProfileModel serializes and deserializes JSON correctly', () {
      final profile = UserDiscoveryProfileModel(
        userId: 'actor-json',
        preferredDomains: const [
          DomainPreferenceModel.environment,
          DomainPreferenceModel.justice,
        ],
        complexityLevel: ComplexityLevelModel.deepDeliberation,
        freshnessPreference: FreshnessPreferenceModel.currentEvents,
        realEventPreference: RealEventPreferenceModel.realEventsFirst,
        diversificationBoost: 0.75,
        updatedAt: DateTime.utc(2026, 9, 1, 12, 0),
      );

      final json = profile.toJson();
      final decoded = UserDiscoveryProfileModel.fromJson(json);

      expect(decoded.userId, profile.userId);
      expect(decoded.preferredDomains, profile.preferredDomains);
      expect(decoded.complexityLevel, ComplexityLevelModel.deepDeliberation);
      expect(decoded.freshnessPreference, FreshnessPreferenceModel.currentEvents);
      expect(decoded.realEventPreference, RealEventPreferenceModel.realEventsFirst);
      expect(decoded.diversificationBoost, 0.75);
    });

    testWidgets('UserDiscoveryProfileSheet renders and handles interactions in TR', (tester) async {
      final profile = UserDiscoveryProfileModel(
        userId: 'actor-widget',
        preferredDomains: const [
          DomainPreferenceModel.civic,
          DomainPreferenceModel.technology,
        ],
        complexityLevel: ComplexityLevelModel.balanced,
        freshnessPreference: FreshnessPreferenceModel.balanced,
        realEventPreference: RealEventPreferenceModel.balanced,
        diversificationBoost: 0.6,
        updatedAt: DateTime.utc(2026, 9, 1),
      );

      UserDiscoveryProfileModel? savedResult;

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
          home: Scaffold(
            body: SingleChildScrollView(
              child: UserDiscoveryProfileSheet(
                initialProfile: profile,
                onSave: (p) => savedResult = p,
              ),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(UserDiscoveryProfileSheet), findsOneWidget);
      expect(find.text('Keşif ve Gündem Tercihleri'), findsOneWidget);
      expect(find.text('Yurttaşlık'), findsOneWidget);
      expect(find.text('Teknoloji & Yapay Zekâ'), findsOneWidget);

      // Tap on save button
      await tester.tap(find.text('Keşif Tercihlerini Kaydet'));
      await tester.pumpAndSettle();

      expect(savedResult, isNotNull);
      expect(savedResult!.userId, 'actor-widget');
    });
  });
}
