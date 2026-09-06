import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/academic_research_portal_models.dart';

void main() {
  group('Academic Research & Open Data Portal (CAP-036)', () {
    test('ADR-0209 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0209-academic-research-portal.md');
      final contract = File('../../docs/contracts/academic-research-portal.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-ACAD-PORTAL-001'));
      expect(contract.readAsStringSync(), contains('ARGUMENT_GRAPH_TOPOLOGY'));
    });

    test('AcademicResearchDatasetModel instantiates properly', () {
      const model = AcademicResearchDatasetModel(
        datasetId: 'ds_1',
        datasetTitle: 'Global Civic Deliberation 2026',
        corpusType: ResearchCorpusTypeModel.argumentGraphTopology,
        recordCount: 125000,
        differentialPrivacyEpsilon: 0.50,
        doiIdentifier: '10.1000/182_kefe',
      );

      expect(model.recordCount, 125000);
      expect(model.corpusType, ResearchCorpusTypeModel.argumentGraphTopology);
    });

    test('InternalAlphaStrings contains Academic Portal localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.acadPortEyebrow, contains('AKADEMİK ARAŞTIRMA'));
      expect(tr.acadPortCorpGraph, contains('Argüman Grafı'));

      const en = KefeStrings(Locale('en'));
      expect(en.acadPortEyebrow, contains('ACADEMIC RESEARCH'));
      expect(en.acadPortCorpGraph, contains('Argument Graph'));
    });
  });
}
