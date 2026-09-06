enum SignalQualificationStatusModel {
  qualified,
  provisional,
  disqualified;

  static SignalQualificationStatusModel fromString(String value) {
    return switch (value.toUpperCase()) {
      'QUALIFIED' => SignalQualificationStatusModel.qualified,
      'PROVISIONAL' => SignalQualificationStatusModel.provisional,
      _ => SignalQualificationStatusModel.disqualified,
    };
  }
}

enum SignalQualificationTierModel {
  goldStandard,
  silverValidated,
  bronzeObserved,
  unqualified;

  static SignalQualificationTierModel fromString(String value) {
    return switch (value.toUpperCase()) {
      'GOLD_STANDARD' => SignalQualificationTierModel.goldStandard,
      'SILVER_VALIDATED' => SignalQualificationTierModel.silverValidated,
      'BRONZE_OBSERVED' => SignalQualificationTierModel.bronzeObserved,
      _ => SignalQualificationTierModel.unqualified,
    };
  }
}

class QualificationCriterionModel {
  const QualificationCriterionModel({
    required this.criterionId,
    required this.nameTr,
    required this.nameEn,
    required this.score,
    required this.threshold,
    required this.isPassed,
    required this.auditNote,
  });

  final String criterionId;
  final String nameTr;
  final String nameEn;
  final double score;
  final double threshold;
  final bool isPassed;
  final String auditNote;

  factory QualificationCriterionModel.fromJson(Map<String, dynamic> json) {
    return QualificationCriterionModel(
      criterionId: json['criterion_id'] as String,
      nameTr: json['name_tr'] as String,
      nameEn: json['name_en'] as String,
      score: (json['score'] as num).toDouble(),
      threshold: (json['threshold'] as num).toDouble(),
      isPassed: json['is_passed'] as bool,
      auditNote: json['audit_note'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'criterion_id': criterionId,
    'name_tr': nameTr,
    'name_en': nameEn,
    'score': score,
    'threshold': threshold,
    'is_passed': isPassed,
    'audit_note': auditNote,
  };
}

class SignalQualificationReportModel {
  const SignalQualificationReportModel({
    required this.signalId,
    required this.caseVersionId,
    required this.caseTitle,
    required this.qualificationStatus,
    required this.qualificationTier,
    required this.overallScore,
    required this.sampleSize,
    required this.criteria,
    required this.eligibleChannels,
    required this.certifiedAt,
    required this.qualificationAuditHash,
  });

  final String signalId;
  final String caseVersionId;
  final String caseTitle;
  final SignalQualificationStatusModel qualificationStatus;
  final SignalQualificationTierModel qualificationTier;
  final double overallScore;
  final int sampleSize;
  final List<QualificationCriterionModel> criteria;
  final List<String> eligibleChannels;
  final String certifiedAt;
  final String qualificationAuditHash;

  factory SignalQualificationReportModel.fromJson(Map<String, dynamic> json) {
    return SignalQualificationReportModel(
      signalId: json['signal_id'] as String,
      caseVersionId: json['case_version_id'] as String,
      caseTitle: json['case_title'] as String,
      qualificationStatus: SignalQualificationStatusModel.fromString(
        json['qualification_status'] as String,
      ),
      qualificationTier: SignalQualificationTierModel.fromString(
        json['qualification_tier'] as String,
      ),
      overallScore: (json['overall_score'] as num).toDouble(),
      sampleSize: json['sample_size'] as int,
      criteria: (json['criteria'] as List<dynamic>)
          .map((c) => QualificationCriterionModel.fromJson(c as Map<String, dynamic>))
          .toList(),
      eligibleChannels: (json['eligible_channels'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      certifiedAt: json['certified_at'] as String,
      qualificationAuditHash: json['qualification_audit_hash'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'signal_id': signalId,
    'case_version_id': caseVersionId,
    'case_title': caseTitle,
    'qualification_status': switch (qualificationStatus) {
      SignalQualificationStatusModel.qualified => 'QUALIFIED',
      SignalQualificationStatusModel.provisional => 'PROVISIONAL',
      SignalQualificationStatusModel.disqualified => 'DISQUALIFIED',
    },
    'qualification_tier': switch (qualificationTier) {
      SignalQualificationTierModel.goldStandard => 'GOLD_STANDARD',
      SignalQualificationTierModel.silverValidated => 'SILVER_VALIDATED',
      SignalQualificationTierModel.bronzeObserved => 'BRONZE_OBSERVED',
      SignalQualificationTierModel.unqualified => 'UNQUALIFIED',
    },
    'overall_score': overallScore,
    'sample_size': sampleSize,
    'criteria': criteria.map((c) => c.toJson()).toList(),
    'eligible_channels': eligibleChannels,
    'certified_at': certifiedAt,
    'qualification_audit_hash': qualificationAuditHash,
  };
}
