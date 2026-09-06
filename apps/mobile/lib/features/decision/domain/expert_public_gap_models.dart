class ExpertPublicGapModel {
  const ExpertPublicGapModel({
    required this.caseVersionId,
    required this.expertSampleSize,
    required this.publicSampleSize,
    required this.expertDistribution,
    required this.publicDistribution,
    required this.gapMagnitudePoints,
    required this.gapClassification,
    required this.keyDivergenceDrivers,
    required this.epistemicBridges,
    required this.generatedAt,
  });

  factory ExpertPublicGapModel.fromJson(Map<String, dynamic> json) {
    final rawExpert =
        json['expert_distribution'] as Map<String, dynamic>? ?? {};
    final expert = <String, double>{};
    for (final entry in rawExpert.entries) {
      if (entry.value is num) {
        expert[entry.key] = (entry.value as num).toDouble();
      }
    }

    final rawPublic =
        json['public_distribution'] as Map<String, dynamic>? ?? {};
    final public = <String, double>{};
    for (final entry in rawPublic.entries) {
      if (entry.value is num) {
        public[entry.key] = (entry.value as num).toDouble();
      }
    }

    final rawDrivers =
        json['key_divergence_drivers'] as List<dynamic>? ?? const [];
    final rawBridges = json['epistemic_bridges'] as List<dynamic>? ?? const [];

    return ExpertPublicGapModel(
      caseVersionId: json['case_version_id'] as String? ?? '',
      expertSampleSize: (json['expert_sample_size'] as num?)?.toInt() ?? 0,
      publicSampleSize: (json['public_sample_size'] as num?)?.toInt() ?? 0,
      expertDistribution: expert,
      publicDistribution: public,
      gapMagnitudePoints:
          (json['gap_magnitude_points'] as num?)?.toInt() ?? 0,
      gapClassification:
          json['gap_classification'] as String? ?? 'CONVERGENT',
      keyDivergenceDrivers: rawDrivers.whereType<String>().toList(growable: false),
      epistemicBridges: rawBridges.whereType<String>().toList(growable: false),
      generatedAt: json['generated_at'] as String? ?? '',
    );
  }

  final String caseVersionId;
  final int expertSampleSize;
  final int publicSampleSize;
  final Map<String, double> expertDistribution;
  final Map<String, double> publicDistribution;
  final int gapMagnitudePoints;
  final String gapClassification;
  final List<String> keyDivergenceDrivers;
  final List<String> epistemicBridges;
  final String generatedAt;

  Map<String, dynamic> toJson() => {
    'case_version_id': caseVersionId,
    'expert_sample_size': expertSampleSize,
    'public_sample_size': publicSampleSize,
    'expert_distribution': expertDistribution,
    'public_distribution': publicDistribution,
    'gap_magnitude_points': gapMagnitudePoints,
    'gap_classification': gapClassification,
    'key_divergence_drivers': keyDivergenceDrivers,
    'epistemic_bridges': epistemicBridges,
    'generated_at': generatedAt,
  };
}
