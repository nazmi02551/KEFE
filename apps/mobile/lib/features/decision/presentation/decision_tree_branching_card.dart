import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/decision_tree_branching_models.dart';

class DecisionTreeBranchingCard extends StatelessWidget {
  const DecisionTreeBranchingCard({
    required this.node,
    this.onTap,
    super.key,
  });

  final DecisionTreeNodeModel node;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _nodeColor(visual, node.nodeType);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('tree-node-${node.treeId}'),
        tone: KefeSurfaceTone.raised,
        padding: const EdgeInsets.all(18),
        borderRadius: 22,
        accent: accent,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: accent.withValues(alpha: visual.isDark ? 0.18 : 0.10),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: accent.withValues(alpha: 0.3)),
                  ),
                  child: Icon(Icons.account_tree_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.treeBranchEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _nodeLabel(strings, node.nodeType),
                        style: TextStyle(
                          fontSize: 12.5,
                          fontWeight: FontWeight.w800,
                          color: visual.foreground,
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
                  decoration: BoxDecoration(
                    color: visual.surfaceSunken,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                  ),
                  child: Text(
                    strings.treeBranchProbLabel((node.branchProbability * 100).toInt()),
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w800,
                      color: accent,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              node.nodeLabel,
              style: TextStyle(
                fontSize: 12.5,
                fontWeight: FontWeight.w800,
                color: visual.foreground,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: visual.surfaceSunken,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: visual.border.withValues(alpha: 0.5)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    strings.treeBranchImpactLabel,
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      color: visual.gold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    node.projectedImpactSummary,
                    style: TextStyle(
                      fontSize: 11.5,
                      color: visual.foreground,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _nodeColor(KefeVisualSystem visual, TreeNodeTypeModel type) => switch (type) {
    TreeNodeTypeModel.primaryDecisionFork => visual.rules,
    TreeNodeTypeModel.contingencyBranch => visual.gold,
    TreeNodeTypeModel.terminalOutcomeLeaf => visual.empathy,
  };

  String _nodeLabel(KefeStrings strings, TreeNodeTypeModel type) => switch (type) {
    TreeNodeTypeModel.primaryDecisionFork => strings.treeBranchNodeFork,
    TreeNodeTypeModel.contingencyBranch => strings.treeBranchNodeContingency,
    TreeNodeTypeModel.terminalOutcomeLeaf => strings.treeBranchNodeTerminal,
  };
}
