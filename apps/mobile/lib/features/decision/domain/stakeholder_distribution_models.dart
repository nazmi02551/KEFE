class StakeholderDistributionItemModel {
  const StakeholderDistributionItemModel({
    required this.category,
    required this.name,
    required this.participantCount,
    required this.sampleShare,
    required this.optionShares,
    required this.primaryChoice,
    required this.cohesionIndex,
    required this.divergenceFromOverallPoints,
  });

  factory StakeholderDistributionItemModel.fromJson(Map<String, dynamic> json) {
    final rawShares = json['option_shares'] as Map<String, dynamic>? ?? {};
    final shares = <String, double>{};
    for (final entry in rawShares.entries) {
      if (entry.value is num) {
        shares[entry.key] = (entry.value as num).toDouble();
      }
    }

    return StakeholderDistributionItemModel(
      category: json['category'] as String? ?? 'CIVIC_COMMUNITY',
      name: json['name'] as String? ?? '',
      participantCount: (json['participant_count'] as num?)?.toInt() ?? 0,
      sampleShare: (json['sample_share'] as num?)?.toDouble() ?? 0.0,
      optionShares: shares,
      primaryChoice: json['primary_choice'] as String? ?? '',
      cohesionIndex: (json['cohesion_index'] as num?)?.toDouble() ?? 0.0,
      divergenceFromOverallPoints:
          (json['divergence_from_overall_points'] as num?)?.toInt() ?? 0,
    );
  }

  final String category;
  final String name;
  final int participantCount;
  final double sampleShare;
  final Map<String, double> optionShares;
  final String primaryChoice;
  final double cohesionIndex;
  final int divergenceFromOverallPoints;

  Map<String, dynamic> toJson() => {
    'category': category,
    'name': name,
    'participant_count': participantCount,
    'sample_share': sampleShare,
    'option_shares': optionShares,
    'primary_choice': primaryChoice,
    'cohesion_index': cohesionIndex,
    'divergence_from_overall_points': divergenceFromOverallPoints,
  };
}

class StakeholderDistributionModel {
  const StakeholderDistributionModel({
    required this.caseVersionId,
    required this.totalStakeholdersRepresented,
    required this.activeCategoriesCount,
    required this.stakeholderDistributions,
    required this.pluralismScore,
    required this.generatedAt,
  });

  factory StakeholderDistributionModel.fromJson(Map<String, dynamic> json) {
    final rawItems =
        json['stakeholder_distributions'] as List<dynamic>? ?? const [];

    return StakeholderDistributionModel(
      caseVersionId: json['case_version_id'] as String? ?? '',
      totalStakeholdersRepresented:
          (json['total_stakeholders_represented'] as num?)?.toInt() ?? 0,
      activeCategoriesCount:
          (json['active_categories_count'] as num?)?.toInt() ?? 0,
      stakeholderDistributions: rawItems
          .whereType<Map<String, dynamic>>()
          .map(StakeholderDistributionItemModel.fromJson)
          .toList(growable: false),
      pluralismScore: (json['pluralism_score'] as num?)?.toDouble() ?? 0.0,
      generatedAt: json['generated_at'] as String? ?? '',
    );
  }

  final String caseVersionId;
  final int totalStakeholdersRepresented;
  final int activeCategoriesCount;
  final List<StakeholderDistributionItemModel> stakeholderDistributions;
  final double pluralismScore;
  final String generatedAt;

  Map<String, dynamic> toJson() => {
    'case_version_id': caseVersionId,
    'total_stakeholders_represented': totalStakeholdersRepresented,
    'active_categories_count': activeCategoriesCount,
    'stakeholder_distributions':
        stakeholderDistributions.map((s) => s.toJson()).toList(),
    'pluralism_score': pluralismScore,
    'generated_at': generatedAt,
  };
}
