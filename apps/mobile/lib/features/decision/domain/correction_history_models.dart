import 'package:flutter/foundation.dart';

enum CorrectionTypeModel {
  factualUpdate,
  clarification,
  sourceExpansion,
  typoFix,
  legalStatusUpdate;

  static CorrectionTypeModel fromString(String val) =>
      switch (val.toUpperCase()) {
        'CLARIFICATION' => clarification,
        'SOURCE_EXPANSION' => sourceExpansion,
        'TYPO_FIX' => typoFix,
        'LEGAL_STATUS_UPDATE' => legalStatusUpdate,
        _ => factualUpdate,
      };

  String get serializedName => switch (this) {
    factualUpdate => 'FACTUAL_UPDATE',
    clarification => 'CLARIFICATION',
    sourceExpansion => 'SOURCE_EXPANSION',
    typoFix => 'TYPO_FIX',
    legalStatusUpdate => 'LEGAL_STATUS_UPDATE',
  };
}

enum CorrectionSeverityModel {
  minor,
  material,
  substantial;

  static CorrectionSeverityModel fromString(String val) =>
      switch (val.toUpperCase()) {
        'MATERIAL' => material,
        'SUBSTANTIAL' => substantial,
        _ => minor,
      };

  String get serializedName => switch (this) {
    minor => 'MINOR',
    material => 'MATERIAL',
    substantial => 'SUBSTANTIAL',
  };
}

@immutable
class CaseCorrectionItemModel {
  const CaseCorrectionItemModel({
    required this.correctionId,
    required this.caseVersionId,
    required this.correctionType,
    required this.severity,
    required this.summary,
    required this.editorialRationale,
    required this.timestamp,
    this.previousText,
    this.correctedText,
  });

  final String correctionId;
  final String caseVersionId;
  final CorrectionTypeModel correctionType;
  final CorrectionSeverityModel severity;
  final String summary;
  final String editorialRationale;
  final DateTime timestamp;
  final String? previousText;
  final String? correctedText;

  factory CaseCorrectionItemModel.fromJson(Map<String, dynamic> json) =>
      CaseCorrectionItemModel(
        correctionId: json['correction_id'] as String? ?? '',
        caseVersionId: json['case_version_id'] as String? ?? '',
        correctionType: CorrectionTypeModel.fromString(
          json['correction_type'] as String? ?? '',
        ),
        severity: CorrectionSeverityModel.fromString(
          json['severity'] as String? ?? '',
        ),
        summary: json['summary'] as String? ?? '',
        editorialRationale: json['editorial_rationale'] as String? ?? '',
        timestamp:
            DateTime.tryParse(json['timestamp'] as String? ?? '')?.toUtc() ??
            DateTime.now().toUtc(),
        previousText: json['previous_text'] as String?,
        correctedText: json['corrected_text'] as String?,
      );

  Map<String, dynamic> toJson() => {
    'correction_id': correctionId,
    'case_version_id': caseVersionId,
    'correction_type': correctionType.serializedName,
    'severity': severity.serializedName,
    'summary': summary,
    'editorial_rationale': editorialRationale,
    'timestamp': timestamp.toIso8601String(),
    if (previousText != null) 'previous_text': previousText,
    if (correctedText != null) 'corrected_text': correctedText,
  };
}

@immutable
class CaseCorrectionHistoryModel {
  const CaseCorrectionHistoryModel({
    required this.caseVersionId,
    required this.corrections,
  });

  final String caseVersionId;
  final List<CaseCorrectionItemModel> corrections;

  factory CaseCorrectionHistoryModel.fromJson(Map<String, dynamic> json) =>
      CaseCorrectionHistoryModel(
        caseVersionId: json['case_version_id'] as String? ?? '',
        corrections:
            (json['corrections'] as List<dynamic>?)
                ?.map(
                  (c) => CaseCorrectionItemModel.fromJson(
                    c as Map<String, dynamic>,
                  ),
                )
                .toList(growable: false) ??
            const [],
      );

  Map<String, dynamic> toJson() => {
    'case_version_id': caseVersionId,
    'corrections': corrections.map((c) => c.toJson()).toList(),
  };
}
