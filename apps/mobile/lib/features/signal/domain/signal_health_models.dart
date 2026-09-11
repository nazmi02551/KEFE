import 'package:flutter/foundation.dart';

enum SignalQualificationStatusModel {
  qualifiedSignal,
  provisionalTrend,
  unqualifiedNoise;

  static SignalQualificationStatusModel fromString(String val) =>
      switch (val.toUpperCase()) {
        'PROVISIONAL_TREND' => provisionalTrend,
        'UNQUALIFIED_NOISE' => unqualifiedNoise,
        _ => qualifiedSignal,
      };

  String get serializedName => switch (this) {
    qualifiedSignal => 'QUALIFIED_SIGNAL',
    provisionalTrend => 'PROVISIONAL_TREND',
    unqualifiedNoise => 'UNQUALIFIED_NOISE',
  };
}

@immutable
class SignalHealthDimensionModel {
  const SignalHealthDimensionModel({
    required this.dimensionId,
    required this.titleTr,
    required this.titleEn,
    required this.score,
    required this.threshold,
    required this.isPassed,
    required this.detail,
  });

  final String dimensionId;
  final String titleTr;
  final String titleEn;
  final double score;
  final double threshold;
  final bool isPassed;
  final String detail;

  /// Returns the locale-appropriate title.
  ///
  /// Falls back to [titleEn] for unsupported locales (AGENTS.md §9:
  /// "unsupported lookup has deterministic English fallback").
  /// Raw backend values are not mutated — only sunum selection changes.
  String localizedTitle(String languageCode) =>
      languageCode == 'tr' ? titleTr : titleEn;

  factory SignalHealthDimensionModel.fromJson(Map<String, dynamic> json) =>
      SignalHealthDimensionModel(
        dimensionId: json['dimension_id'] as String? ?? '',
        titleTr: json['title_tr'] as String? ?? '',
        titleEn: json['title_en'] as String? ?? '',
        score: (json['score'] as num?)?.toDouble() ?? 0.0,
        threshold: (json['threshold'] as num?)?.toDouble() ?? 0.0,
        isPassed: json['is_passed'] as bool? ?? false,
        detail: json['detail'] as String? ?? '',
      );

  Map<String, dynamic> toJson() => {
    'dimension_id': dimensionId,
    'title_tr': titleTr,
    'title_en': titleEn,
    'score': score,
    'threshold': threshold,
    'is_passed': isPassed,
    'detail': detail,
  };
}

@immutable
class SignalHealthReportModel {
  const SignalHealthReportModel({
    required this.signalId,
    required this.caseVersionId,
    required this.overallQualification,
    required this.overallHealthScore,
    required this.sampleSize,
    required this.dimensions,
    required this.certifiedAt,
    required this.methodologyHash,
  });

  final String signalId;
  final String caseVersionId;
  final SignalQualificationStatusModel overallQualification;
  final double overallHealthScore;
  final int sampleSize;
  final List<SignalHealthDimensionModel> dimensions;
  final DateTime certifiedAt;
  final String methodologyHash;

  bool get isQualified =>
      overallQualification == SignalQualificationStatusModel.qualifiedSignal;

  factory SignalHealthReportModel.fromJson(Map<String, dynamic> json) =>
      SignalHealthReportModel(
        signalId: json['signal_id'] as String? ?? '',
        caseVersionId: json['case_version_id'] as String? ?? '',
        overallQualification: SignalQualificationStatusModel.fromString(
          json['overall_qualification'] as String? ?? '',
        ),
        overallHealthScore:
            (json['overall_health_score'] as num?)?.toDouble() ?? 0.0,
        sampleSize: (json['sample_size'] as num?)?.toInt() ?? 0,
        dimensions: (json['dimensions'] as List<dynamic>? ?? const [])
            .map((e) => SignalHealthDimensionModel.fromJson(e as Map<String, dynamic>))
            .toList(),
        certifiedAt:
            DateTime.tryParse(json['certified_at'] as String? ?? '')?.toUtc() ??
            DateTime.now().toUtc(),
        methodologyHash: json['methodology_hash'] as String? ?? '',
      );

  Map<String, dynamic> toJson() => {
    'signal_id': signalId,
    'case_version_id': caseVersionId,
    'overall_qualification': overallQualification.serializedName,
    'overall_health_score': overallHealthScore,
    'sample_size': sampleSize,
    'dimensions': dimensions.map((d) => d.toJson()).toList(),
    'certified_at': certifiedAt.toIso8601String(),
    'methodology_hash': methodologyHash,
  };
}
