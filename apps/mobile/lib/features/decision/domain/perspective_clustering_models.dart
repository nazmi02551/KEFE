class PerspectiveClusterModel {
  const PerspectiveClusterModel({
    required this.clusterId,
    required this.caseVersionId,
    required this.archetype,
    required this.coreThesis,
    required this.argumentCount,
    required this.supportPercentage,
  });

  factory PerspectiveClusterModel.fromJson(Map<String, dynamic> json) {
    return PerspectiveClusterModel(
      clusterId: json['cluster_id'] as String? ?? '',
      caseVersionId: json['case_version_id'] as String? ?? '',
      archetype: json['archetype'] as String? ?? 'NEAR_CONSENSUS',
      coreThesis: json['core_thesis'] as String? ?? '',
      argumentCount: (json['argument_count'] as num?)?.toInt() ?? 0,
      supportPercentage: (json['support_percentage'] as num?)?.toDouble() ?? 0.0,
    );
  }

  final String clusterId;
  final String caseVersionId;
  final String archetype;
  final String coreThesis;
  final int argumentCount;
  final double supportPercentage;

  Map<String, dynamic> toJson() => {
    'cluster_id': clusterId,
    'case_version_id': caseVersionId,
    'archetype': archetype,
    'core_thesis': coreThesis,
    'argument_count': argumentCount,
    'support_percentage': supportPercentage,
  };
}

class CaseClusteringModel {
  const CaseClusteringModel({
    required this.caseVersionId,
    required this.totalArgumentsClustered,
    required this.clusters,
  });

  factory CaseClusteringModel.fromJson(Map<String, dynamic> json) {
    final rawClusters = json['clusters'] as List<dynamic>? ?? const [];
    return CaseClusteringModel(
      caseVersionId: json['case_version_id'] as String? ?? '',
      totalArgumentsClustered: (json['total_arguments_clustered'] as num?)?.toInt() ?? 0,
      clusters: rawClusters
          .whereType<Map<String, dynamic>>()
          .map(PerspectiveClusterModel.fromJson)
          .toList(growable: false),
    );
  }

  final String caseVersionId;
  final int totalArgumentsClustered;
  final List<PerspectiveClusterModel> clusters;

  Map<String, dynamic> toJson() => {
    'case_version_id': caseVersionId,
    'total_arguments_clustered': totalArgumentsClustered,
    'clusters': clusters.map((c) => c.toJson()).toList(),
  };
}
