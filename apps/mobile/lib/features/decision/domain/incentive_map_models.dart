class IncentiveNodeModel {
  const IncentiveNodeModel({
    required this.stakeholderGroup,
    required this.coreIncentive,
    required this.incentiveType,
    required this.alignmentStatus,
    required this.intensityScore,
    this.unintendedBehavior = '',
  });

  factory IncentiveNodeModel.fromJson(Map<String, dynamic> json) {
    return IncentiveNodeModel(
      stakeholderGroup: json['stakeholder_group'] as String? ?? '',
      coreIncentive: json['core_incentive'] as String? ?? '',
      incentiveType: json['incentive_type'] as String? ?? 'FINANCIAL_PROFIT',
      alignmentStatus: json['alignment_status'] as String? ?? 'ALIGNED',
      intensityScore: (json['intensity_score'] as num?)?.toDouble() ?? 0.0,
      unintendedBehavior: json['unintended_behavior'] as String? ?? '',
    );
  }

  final String stakeholderGroup;
  final String coreIncentive;
  final String incentiveType;
  final String alignmentStatus;
  final double intensityScore;
  final String unintendedBehavior;

  Map<String, dynamic> toJson() => {
    'stakeholder_group': stakeholderGroup,
    'core_incentive': coreIncentive,
    'incentive_type': incentiveType,
    'alignment_status': alignmentStatus,
    'intensity_score': intensityScore,
    'unintended_behavior': unintendedBehavior,
  };
}

class IncentiveMapModel {
  const IncentiveMapModel({
    required this.mapId,
    required this.caseVersionId,
    required this.alignmentIndex,
    required this.perverseIncentiveRisk,
    required this.primaryDriver,
    required this.mitigationMechanism,
    required this.incentiveNodes,
  });

  factory IncentiveMapModel.fromJson(Map<String, dynamic> json) {
    final nodesRaw = json['incentive_nodes'] as List<dynamic>? ?? const [];
    return IncentiveMapModel(
      mapId: json['map_id'] as String? ?? '',
      caseVersionId: json['case_version_id'] as String? ?? '',
      alignmentIndex: (json['alignment_index'] as num?)?.toDouble() ?? 0.0,
      perverseIncentiveRisk: json['perverse_incentive_risk'] as String? ?? 'MODERATE',
      primaryDriver: json['primary_driver'] as String? ?? '',
      mitigationMechanism: json['mitigation_mechanism'] as String? ?? '',
      incentiveNodes: nodesRaw
          .whereType<Map<String, dynamic>>()
          .map(IncentiveNodeModel.fromJson)
          .toList(growable: false),
    );
  }

  final String mapId;
  final String caseVersionId;
  final double alignmentIndex;
  final String perverseIncentiveRisk;
  final String primaryDriver;
  final String mitigationMechanism;
  final List<IncentiveNodeModel> incentiveNodes;

  Map<String, dynamic> toJson() => {
    'map_id': mapId,
    'case_version_id': caseVersionId,
    'alignment_index': alignmentIndex,
    'perverse_incentive_risk': perverseIncentiveRisk,
    'primary_driver': primaryDriver,
    'mitigation_mechanism': mitigationMechanism,
    'incentive_nodes': incentiveNodes.map((n) => n.toJson()).toList(),
  };
}
