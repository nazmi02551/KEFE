import 'package:flutter/foundation.dart';

enum ObjectionCategoryModel {
  editorialBiasFraming,
  factualInaccuracy,
  excludedStakeholder,
  ambiguousOptions,
  depreciatedContext;

  static ObjectionCategoryModel fromString(String val) =>
      switch (val.toUpperCase()) {
        'FACTUAL_INACCURACY' => factualInaccuracy,
        'EXCLUDED_STAKEHOLDER' => excludedStakeholder,
        'AMBIGUOUS_OPTIONS' => ambiguousOptions,
        'DEPRECIATED_CONTEXT' => depreciatedContext,
        _ => editorialBiasFraming,
      };

  String get serializedName => switch (this) {
    editorialBiasFraming => 'EDITORIAL_BIAS_FRAMING',
    factualInaccuracy => 'FACTUAL_INACCURACY',
    excludedStakeholder => 'EXCLUDED_STAKEHOLDER',
    ambiguousOptions => 'AMBIGUOUS_OPTIONS',
    depreciatedContext => 'DEPRECIATED_CONTEXT',
  };
}

enum ObjectionStatusModel {
  submitted,
  underReview,
  acceptedCorrectionFiled,
  rejectedWithReason;

  static ObjectionStatusModel fromString(String val) =>
      switch (val.toUpperCase()) {
        'UNDER_REVIEW' => underReview,
        'ACCEPTED_CORRECTION_FILED' => acceptedCorrectionFiled,
        'REJECTED_WITH_REASON' => rejectedWithReason,
        _ => submitted,
      };

  String get serializedName => switch (this) {
    submitted => 'SUBMITTED',
    underReview => 'UNDER_REVIEW',
    acceptedCorrectionFiled => 'ACCEPTED_CORRECTION_FILED',
    rejectedWithReason => 'REJECTED_WITH_REASON',
  };
}

@immutable
class CaseObjectionItemModel {
  const CaseObjectionItemModel({
    required this.objectionId,
    required this.caseVersionId,
    required this.reasonCategory,
    required this.statement,
    required this.status,
    required this.createdAt,
    this.supportingEvidenceUrl,
    this.resolutionNote,
  });

  final String objectionId;
  final String caseVersionId;
  final ObjectionCategoryModel reasonCategory;
  final String statement;
  final ObjectionStatusModel status;
  final DateTime createdAt;
  final String? supportingEvidenceUrl;
  final String? resolutionNote;

  factory CaseObjectionItemModel.fromJson(Map<String, dynamic> json) =>
      CaseObjectionItemModel(
        objectionId: json['objection_id'] as String? ?? '',
        caseVersionId: json['case_version_id'] as String? ?? '',
        reasonCategory: ObjectionCategoryModel.fromString(
          json['reason_category'] as String? ?? '',
        ),
        statement: json['statement'] as String? ?? '',
        status: ObjectionStatusModel.fromString(
          json['status'] as String? ?? '',
        ),
        createdAt:
            DateTime.tryParse(json['created_at'] as String? ?? '')?.toUtc() ??
            DateTime.now().toUtc(),
        supportingEvidenceUrl: json['supporting_evidence_url'] as String?,
        resolutionNote: json['resolution_note'] as String?,
      );

  Map<String, dynamic> toJson() => {
    'objection_id': objectionId,
    'case_version_id': caseVersionId,
    'reason_category': reasonCategory.serializedName,
    'statement': statement,
    'status': status.serializedName,
    'created_at': createdAt.toIso8601String(),
    if (supportingEvidenceUrl != null)
      'supporting_evidence_url': supportingEvidenceUrl,
    if (resolutionNote != null) 'resolution_note': resolutionNote,
  };
}
