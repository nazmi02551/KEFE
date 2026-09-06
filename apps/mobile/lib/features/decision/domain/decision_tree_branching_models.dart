import 'package:flutter/foundation.dart';

enum TreeNodeTypeModel {
  primaryDecisionFork,
  contingencyBranch,
  terminalOutcomeLeaf,
}

@immutable
class DecisionTreeNodeModel {
  const DecisionTreeNodeModel({
    required this.treeId,
    required this.rootCaseId,
    required this.nodeLabel,
    required this.nodeType,
    required this.branchProbability,
    required this.projectedImpactSummary,
  });

  final String treeId;
  final String rootCaseId;
  final String nodeLabel;
  final TreeNodeTypeModel nodeType;
  final double branchProbability;
  final String projectedImpactSummary;
}
