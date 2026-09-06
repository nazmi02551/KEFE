class ActorResponsibilityModel {
  const ActorResponsibilityModel({
    required this.actorKey,
    required this.actorName,
    required this.responsibilityShare,
    required this.dutyNature,
    required this.jurisdictionScope,
    this.accountabilityMechanism = '',
  });

  factory ActorResponsibilityModel.fromJson(Map<String, dynamic> json) {
    return ActorResponsibilityModel(
      actorKey: json['actor_key'] as String? ?? '',
      actorName: json['actor_name'] as String? ?? '',
      responsibilityShare: (json['responsibility_share'] as num?)?.toDouble() ?? 0.0,
      dutyNature: json['duty_nature'] as String? ?? 'LEGAL_LIABILITY',
      jurisdictionScope: json['jurisdiction_scope'] as String? ?? '',
      accountabilityMechanism: json['accountability_mechanism'] as String? ?? '',
    );
  }

  final String actorKey;
  final String actorName;
  final double responsibilityShare;
  final String dutyNature;
  final String jurisdictionScope;
  final String accountabilityMechanism;

  Map<String, dynamic> toJson() => {
    'actor_key': actorKey,
    'actor_name': actorName,
    'responsibility_share': responsibilityShare,
    'duty_nature': dutyNature,
    'jurisdiction_scope': jurisdictionScope,
    'accountability_mechanism': accountabilityMechanism,
  };
}

class ResponsibilityAnalysisModel {
  const ResponsibilityAnalysisModel({
    required this.analysisId,
    required this.caseVersionId,
    required this.clarityScore,
    required this.hasAccountabilityGap,
    required this.legalRedressChannel,
    required this.actorAllocations,
    this.gapExplanation,
  });

  factory ResponsibilityAnalysisModel.fromJson(Map<String, dynamic> json) {
    final rawAllocations = json['actor_allocations'] as List<dynamic>? ?? const [];
    return ResponsibilityAnalysisModel(
      analysisId: json['analysis_id'] as String? ?? '',
      caseVersionId: json['case_version_id'] as String? ?? '',
      clarityScore: (json['clarity_score'] as num?)?.toDouble() ?? 0.0,
      hasAccountabilityGap: json['has_accountability_gap'] as bool? ?? false,
      legalRedressChannel: json['legal_redress_channel'] as String? ?? '',
      gapExplanation: json['gap_explanation'] as String?,
      actorAllocations: rawAllocations
          .whereType<Map<String, dynamic>>()
          .map(ActorResponsibilityModel.fromJson)
          .toList(growable: false),
    );
  }

  final String analysisId;
  final String caseVersionId;
  final double clarityScore;
  final bool hasAccountabilityGap;
  final String legalRedressChannel;
  final String? gapExplanation;
  final List<ActorResponsibilityModel> actorAllocations;

  Map<String, dynamic> toJson() => {
    'analysis_id': analysisId,
    'case_version_id': caseVersionId,
    'clarity_score': clarityScore,
    'has_accountability_gap': hasAccountabilityGap,
    'legal_redress_channel': legalRedressChannel,
    'gap_explanation': gapExplanation,
    'actor_allocations': actorAllocations.map((a) => a.toJson()).toList(),
  };
}
