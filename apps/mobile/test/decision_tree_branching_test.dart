import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/decision_tree_branching_models.dart';

void main() {
  group('Decision Tree & Scenario Branching Graph (CAP-099)', () {
    test('ADR-0212 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0212-decision-tree-branching.md');
      final contract = File('../../docs/contracts/decision-tree-branching.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-TREE-BRANCH-001'));
      expect(contract.readAsStringSync(), contains('PRIMARY_DECISION_FORK'));
    });

    test('DecisionTreeNodeModel instantiates properly', () {
      const model = DecisionTreeNodeModel(
        treeId: 'tree_1',
        rootCaseId: 'case_1',
        nodeLabel: 'Yenilenebilir Enerji Paketi',
        nodeType: TreeNodeTypeModel.primaryDecisionFork,
        branchProbability: 0.75,
        projectedImpactSummary: 'Karbon emisyonunda %30 azalma.',
      );

      expect(model.branchProbability, 0.75);
      expect(model.nodeType, TreeNodeTypeModel.primaryDecisionFork);
    });

    test('InternalAlphaStrings contains Decision Tree localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.treeBranchEyebrow, contains('KARAR AĞACI'));
      expect(tr.treeBranchNodeFork, contains('Ana Politika'));

      const en = KefeStrings(Locale('en'));
      expect(en.treeBranchEyebrow, contains('DECISION TREE'));
      expect(en.treeBranchNodeFork, contains('Primary Policy'));
    });
  });
}
