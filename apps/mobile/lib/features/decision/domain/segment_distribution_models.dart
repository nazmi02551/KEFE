class SegmentCohortModel {
  const SegmentCohortModel({
    required this.cohortType,
    required this.cohortLabel,
    required this.sampleSize,
    required this.isSuppressed,
    this.suppressionReason,
    required this.optionShares,
    this.primaryChoice,
    required this.entropyScore,
  });

  factory SegmentCohortModel.fromJson(Map<String, dynamic> json) {
    final rawShares = json['option_shares'] as Map<String, dynamic>? ?? {};
    final shares = <String, double>{};
    for (final entry in rawShares.entries) {
      if (entry.value is num) {
        shares[entry.key] = (entry.value as num).toDouble();
      }
    }

    return SegmentCohortModel(
      cohortType: json['cohort_type'] as String? ?? 'AGE_COHORT',
      cohortLabel: json['cohort_label'] as String? ?? '',
      sampleSize: (json['sample_size'] as num?)?.toInt() ?? 0,
      isSuppressed: json['is_suppressed'] as bool? ?? false,
      suppressionReason: json['suppression_reason'] as String?,
      optionShares: shares,
      primaryChoice: json['primary_choice'] as String?,
      entropyScore: (json['entropy_score'] as num?)?.toDouble() ?? 0.0,
    );
  }

  final String cohortType;
  final String cohortLabel;
  final int sampleSize;
  final bool isSuppressed;
  final String? suppressionReason;
  final Map<String, double> optionShares;
  final String? primaryChoice;
  final double entropyScore;

  Map<String, dynamic> toJson() => {
    'cohort_type': cohortType,
    'cohort_label': cohortLabel,
    'sample_size': sampleSize,
    'is_suppressed': isSuppressed,
    'suppression_reason': suppressionReason,
    'option_shares': optionShares,
    'primary_choice': primaryChoice,
    'entropy_score': entropyScore,
  };
}

class PrivacyGuaranteesModel {
  const PrivacyGuaranteesModel({
    required this.kAnonymityThreshold,
    required this.noIndividualProfiling,
    required this.differentialPrivacyNoiseApplied,
  });

  factory PrivacyGuaranteesModel.fromJson(Map<String, dynamic> json) {
    return PrivacyGuaranteesModel(
      kAnonymityThreshold: (json['k_anonymity_threshold'] as num?)?.toInt() ?? 30,
      noIndividualProfiling: json['no_individual_profiling'] as bool? ?? true,
      differentialPrivacyNoiseApplied:
          json['differential_privacy_noise_applied'] as bool? ?? true,
    );
  }

  final int kAnonymityThreshold;
  final bool noIndividualProfiling;
  final bool differentialPrivacyNoiseApplied;

  Map<String, dynamic> toJson() => {
    'k_anonymity_threshold': kAnonymityThreshold,
    'no_individual_profiling': noIndividualProfiling,
    'differential_privacy_noise_applied': differentialPrivacyNoiseApplied,
  };
}

class SegmentDistributionModel {
  const SegmentDistributionModel({
    required this.caseVersionId,
    required this.minimumSampleThreshold,
    required this.overallSampleSize,
    required this.segments,
    required this.privacyGuarantees,
    required this.generatedAt,
  });

  factory SegmentDistributionModel.fromJson(Map<String, dynamic> json) {
    final rawSegments = json['segments'] as List<dynamic>? ?? const [];
    final rawGuarantees = json['privacy_guarantees'] as Map<String, dynamic>? ?? {};

    return SegmentDistributionModel(
      caseVersionId: json['case_version_id'] as String? ?? '',
      minimumSampleThreshold:
          (json['minimum_sample_threshold'] as num?)?.toInt() ?? 30,
      overallSampleSize: (json['overall_sample_size'] as num?)?.toInt() ?? 0,
      segments: rawSegments
          .whereType<Map<String, dynamic>>()
          .map(SegmentCohortModel.fromJson)
          .toList(growable: false),
      privacyGuarantees: PrivacyGuaranteesModel.fromJson(rawGuarantees),
      generatedAt: json['generated_at'] as String? ?? '',
    );
  }

  final String caseVersionId;
  final int minimumSampleThreshold;
  final int overallSampleSize;
  final List<SegmentCohortModel> segments;
  final PrivacyGuaranteesModel privacyGuarantees;
  final String generatedAt;

  Map<String, dynamic> toJson() => {
    'case_version_id': caseVersionId,
    'minimum_sample_threshold': minimumSampleThreshold,
    'overall_sample_size': overallSampleSize,
    'segments': segments.map((s) => s.toJson()).toList(),
    'privacy_guarantees': privacyGuarantees.toJson(),
    'generated_at': generatedAt,
  };
}
