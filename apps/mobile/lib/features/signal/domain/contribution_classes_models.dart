enum ContributionClassIdModel {
  corePreResult,
  exposed,
  advocacySupport;

  static ContributionClassIdModel fromString(String value) {
    return switch (value.toUpperCase()) {
      'CORE_PRE_RESULT' => ContributionClassIdModel.corePreResult,
      'EXPOSED' => ContributionClassIdModel.exposed,
      _ => ContributionClassIdModel.advocacySupport,
    };
  }

  String toApiString() => switch (this) {
    ContributionClassIdModel.corePreResult => 'CORE_PRE_RESULT',
    ContributionClassIdModel.exposed => 'EXPOSED',
    ContributionClassIdModel.advocacySupport => 'ADVOCACY_SUPPORT',
  };
}

class ContributionClassSummaryModel {
  const ContributionClassSummaryModel({
    required this.classId,
    required this.nameTr,
    required this.nameEn,
    required this.count,
    required this.percentage,
    required this.isSignalEligible,
    required this.description,
  });

  final ContributionClassIdModel classId;
  final String nameTr;
  final String nameEn;
  final int count;
  final double percentage;
  final bool isSignalEligible;
  final String description;

  factory ContributionClassSummaryModel.fromJson(Map<String, dynamic> json) {
    return ContributionClassSummaryModel(
      classId: ContributionClassIdModel.fromString(json['class_id'] as String),
      nameTr: json['name_tr'] as String,
      nameEn: json['name_en'] as String,
      count: json['count'] as int,
      percentage: (json['percentage'] as num).toDouble(),
      isSignalEligible: json['is_signal_eligible'] as bool,
      description: json['description'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'class_id': classId.toApiString(),
    'name_tr': nameTr,
    'name_en': nameEn,
    'count': count,
    'percentage': percentage,
    'is_signal_eligible': isSignalEligible,
    'description': description,
  };
}

class ContributionClassesReportModel {
  const ContributionClassesReportModel({
    required this.caseVersionId,
    required this.totalContributions,
    required this.classes,
    required this.contaminationRiskIndex,
    required this.isolationAuditStatus,
    required this.certifiedAt,
    required this.isolationProofHash,
  });

  final String caseVersionId;
  final int totalContributions;
  final List<ContributionClassSummaryModel> classes;
  final double contaminationRiskIndex;
  final String isolationAuditStatus;
  final String certifiedAt;
  final String isolationProofHash;

  factory ContributionClassesReportModel.fromJson(Map<String, dynamic> json) {
    return ContributionClassesReportModel(
      caseVersionId: json['case_version_id'] as String,
      totalContributions: json['total_contributions'] as int,
      classes: (json['classes'] as List<dynamic>)
          .map((c) => ContributionClassSummaryModel.fromJson(c as Map<String, dynamic>))
          .toList(),
      contaminationRiskIndex: (json['contamination_risk_index'] as num).toDouble(),
      isolationAuditStatus: json['isolation_audit_status'] as String,
      certifiedAt: json['certified_at'] as String,
      isolationProofHash: json['isolation_proof_hash'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'case_version_id': caseVersionId,
    'total_contributions': totalContributions,
    'classes': classes.map((c) => c.toJson()).toList(),
    'contamination_risk_index': contaminationRiskIndex,
    'isolation_audit_status': isolationAuditStatus,
    'certified_at': certifiedAt,
    'isolation_proof_hash': isolationProofHash,
  };
}
