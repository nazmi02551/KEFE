import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/perspective_clustering_models.dart';
import 'package:kefe_mobile/features/decision/presentation/perspective_clustering_card.dart';

void main() {
  group('Perspective & Argument Clustering Engine (CAP-033)', () {
    test('ADR-0027 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0027-first-class-claim-argument-normalized-ingestion.md');
      final contract = File('../../docs/contracts/perspective-clustering.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-PERSPECTIVE-CLUSTERING-001'));
      expect(contract.readAsStringSync(), contains('NEAR_CONSENSUS'));
    });

    test('CaseClusteringModel instantiates and serializes properly', () {
      const model = CaseClusteringModel(
        caseVersionId: 'case-ver-cluster-1',
        totalArgumentsClustered: 1000,
        clusters: [
          PerspectiveClusterModel(
            clusterId: 'cluster-1',
            caseVersionId: 'case-ver-cluster-1',
            archetype: 'NEAR_CONSENSUS',
            coreThesis: 'Güvenlik ve kamu yararı önceliklidir.',
            argumentCount: 600,
            supportPercentage: 60.0,
          ),
          PerspectiveClusterModel(
            clusterId: 'cluster-2',
            caseVersionId: 'case-ver-cluster-1',
            archetype: 'OPPOSING_PRINCIPLE',
            coreThesis: 'Bireysel haklar dokunulmazdır.',
            argumentCount: 400,
            supportPercentage: 40.0,
          ),
        ],
      );

      expect(model.caseVersionId, 'case-ver-cluster-1');
      expect(model.totalArgumentsClustered, 1000);
      expect(model.clusters.length, 2);

      final json = model.toJson();
      final roundTrip = CaseClusteringModel.fromJson(json);
      expect(roundTrip.caseVersionId, model.caseVersionId);
      expect(roundTrip.totalArgumentsClustered, 1000);
      expect(roundTrip.clusters.first.archetype, 'NEAR_CONSENSUS');
      expect(roundTrip.clusters.first.supportPercentage, 60.0);
    });

    test('InternalAlphaStrings contains Argument Clustering localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.argClusteringEyebrow, contains('ARGÜMAN KALIP'));
      expect(tr.argClusteringArchetypeNearConsensus, contains('Geniş Mutabakat'));

      const en = KefeStrings(Locale('en'));
      expect(en.argClusteringEyebrow, contains('ARGUMENT PATTERN'));
      expect(en.argClusteringArchetypeNearConsensus, contains('Near-Consensus'));
    });

    testWidgets('PerspectiveClusteringCard renders properly in TR locale', (tester) async {
      const model = CaseClusteringModel(
        caseVersionId: 'case-version-tr-1',
        totalArgumentsClustered: 850,
        clusters: [
          PerspectiveClusterModel(
            clusterId: 'cl-1',
            caseVersionId: 'case-version-tr-1',
            archetype: 'NEAR_CONSENSUS',
            coreThesis: 'Geniş mutabakat kamu yararı çerçevesinde şekilleniyor.',
            argumentCount: 510,
            supportPercentage: 60.0,
          ),
          PerspectiveClusterModel(
            clusterId: 'cl-2',
            caseVersionId: 'case-version-tr-1',
            archetype: 'BRIDGE_SYNTHESIS',
            coreThesis: 'Ortak zemin denetimli kademeli geçiş ile sağlanabilir.',
            argumentCount: 340,
            supportPercentage: 40.0,
          ),
        ],
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
              child: PerspectiveClusteringCard(clustering: model),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byType(PerspectiveClusteringCard), findsOneWidget);
      expect(find.textContaining('ARGÜMAN KALIP'), findsOneWidget);
      expect(find.textContaining('850'), findsOneWidget);
      expect(find.textContaining('Geniş Mutabakat'), findsOneWidget);
      expect(find.textContaining('Ortak Zemin'), findsOneWidget);
    });
  });
}
