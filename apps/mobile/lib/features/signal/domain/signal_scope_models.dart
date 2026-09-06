enum JurisdictionLevelModel {
  municipal,
  regional,
  national,
  transnational;

  static JurisdictionLevelModel fromString(String value) {
    return switch (value.toUpperCase()) {
      'MUNICIPAL' => JurisdictionLevelModel.municipal,
      'REGIONAL' => JurisdictionLevelModel.regional,
      'NATIONAL' => JurisdictionLevelModel.national,
      'TRANSNATIONAL' => JurisdictionLevelModel.transnational,
      _ => JurisdictionLevelModel.municipal,
    };
  }

  String toJsonValue() {
    return switch (this) {
      JurisdictionLevelModel.municipal => 'MUNICIPAL',
      JurisdictionLevelModel.regional => 'REGIONAL',
      JurisdictionLevelModel.national => 'NATIONAL',
      JurisdictionLevelModel.transnational => 'TRANSNATIONAL',
    };
  }
}

enum ScopeAlignmentStatusModel {
  strictlyAligned,
  overbroadWarning,
  mismatchDisqualified;

  static ScopeAlignmentStatusModel fromString(String value) {
    return switch (value.toUpperCase()) {
      'STRICTLY_ALIGNED' => ScopeAlignmentStatusModel.strictlyAligned,
      'OVERBROAD_WARNING' => ScopeAlignmentStatusModel.overbroadWarning,
      'MISMATCH_DISQUALIFIED' => ScopeAlignmentStatusModel.mismatchDisqualified,
      _ => ScopeAlignmentStatusModel.mismatchDisqualified,
    };
  }

  String toJsonValue() {
    return switch (this) {
      ScopeAlignmentStatusModel.strictlyAligned => 'STRICTLY_ALIGNED',
      ScopeAlignmentStatusModel.overbroadWarning => 'OVERBROAD_WARNING',
      ScopeAlignmentStatusModel.mismatchDisqualified => 'MISMATCH_DISQUALIFIED',
    };
  }
}

class ScopeDimensionModel {
  const ScopeDimensionModel({
    required this.dimension,
    required this.declaredScope,
    required this.sampleScope,
    required this.alignmentScore,
    required this.isValid,
  });

  final String dimension;
  final String declaredScope;
  final String sampleScope;
  final double alignmentScore;
  final bool isValid;

  factory ScopeDimensionModel.fromJson(Map<String, dynamic> json) {
    return ScopeDimensionModel(
      dimension: json['dimension'] as String,
      declaredScope: json['declared_scope'] as String,
      sampleScope: json['sample_scope'] as String,
      alignmentScore: (json['alignment_score'] as num).toDouble(),
      isValid: json['is_valid'] as bool,
    );
  }

  Map<String, dynamic> toJson() => {
    'dimension': dimension,
    'declared_scope': declaredScope,
    'sample_scope': sampleScope,
    'alignment_score': alignmentScore,
    'is_valid': isValid,
  };
}

class SignalScopeAlignmentReportModel {
  const SignalScopeAlignmentReportModel({
    required this.signalId,
    required this.caseVersionId,
    required this.jurisdictionLevel,
    required this.targetPopulation,
    required this.geographicScope,
    required this.alignmentStatus,
    required this.overallAlignmentScore,
    required this.dimensions,
    required this.validityWindowDays,
    required this.certifiedAt,
    required this.scopeSealHash,
  });

  final String signalId;
  final String caseVersionId;
  final JurisdictionLevelModel jurisdictionLevel;
  final String targetPopulation;
  final String geographicScope;
  final ScopeAlignmentStatusModel alignmentStatus;
  final double overallAlignmentScore;
  final List<ScopeDimensionModel> dimensions;
  final int validityWindowDays;
  final String certifiedAt;
  final String scopeSealHash;

  factory SignalScopeAlignmentReportModel.fromJson(Map<String, dynamic> json) {
    return SignalScopeAlignmentReportModel(
      signalId: json['signal_id'] as String,
      caseVersionId: json['case_version_id'] as String,
      jurisdictionLevel: JurisdictionLevelModel.fromString(json['jurisdiction_level'] as String),
      targetPopulation: json['target_population'] as String,
      geographicScope: json['geographic_scope'] as String,
      alignmentStatus: ScopeAlignmentStatusModel.fromString(json['alignment_status'] as String),
      overallAlignmentScore: (json['overall_alignment_score'] as num).toDouble(),
      dimensions: (json['dimensions'] as List<dynamic>)
          .map((e) => ScopeDimensionModel.fromJson(e as Map<String, dynamic>))
          .toList(),
      validityWindowDays: json['validity_window_days'] as int,
      certifiedAt: json['certified_at'] as String,
      scopeSealHash: json['scope_seal_hash'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'signal_id': signalId,
    'case_version_id': caseVersionId,
    'jurisdiction_level': jurisdictionLevel.toJsonValue(),
    'target_population': targetPopulation,
    'geographic_scope': geographicScope,
    'alignment_status': alignmentStatus.toJsonValue(),
    'overall_alignment_score': overallAlignmentScore,
    'dimensions': dimensions.map((e) => e.toJson()).toList(),
    'validity_window_days': validityWindowDays,
    'certified_at': certifiedAt,
    'scope_seal_hash': scopeSealHash,
  };
}
