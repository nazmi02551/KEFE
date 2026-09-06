import 'package:flutter/foundation.dart';

enum QualityAuditStatusModel {
  verified,
  pending,
  flagged;

  static QualityAuditStatusModel fromString(String val) =>
      switch (val.toUpperCase()) {
        'FLAGGED' => flagged,
        'PENDING' => pending,
        _ => verified,
      };

  String get serializedName => switch (this) {
    verified => 'VERIFIED',
    pending => 'PENDING',
    flagged => 'FLAGGED',
  };
}

@immutable
class QualityChecklistItemModel {
  const QualityChecklistItemModel({
    required this.dimensionId,
    required this.nameTr,
    required this.nameEn,
    required this.criterionTr,
    required this.criterionEn,
    required this.status,
    required this.reviewerNote,
  });

  final String dimensionId;
  final String nameTr;
  final String nameEn;
  final String criterionTr;
  final String criterionEn;
  final QualityAuditStatusModel status;
  final String reviewerNote;

  factory QualityChecklistItemModel.fromJson(Map<String, dynamic> json) =>
      QualityChecklistItemModel(
        dimensionId: json['dimension_id'] as String? ?? '',
        nameTr: json['name_tr'] as String? ?? '',
        nameEn: json['name_en'] as String? ?? '',
        criterionTr: json['criterion_tr'] as String? ?? '',
        criterionEn: json['criterion_en'] as String? ?? '',
        status: QualityAuditStatusModel.fromString(
          json['status'] as String? ?? '',
        ),
        reviewerNote: json['reviewer_note'] as String? ?? '',
      );

  Map<String, dynamic> toJson() => {
    'dimension_id': dimensionId,
    'name_tr': nameTr,
    'name_en': nameEn,
    'criterion_tr': criterionTr,
    'criterion_en': criterionEn,
    'status': status.serializedName,
    'reviewer_note': reviewerNote,
  };
}

@immutable
class CaseQualityChecklistModel {
  const CaseQualityChecklistModel({
    required this.caseVersionId,
    required this.overallStatus,
    required this.verifiedCount,
    required this.totalCount,
    required this.items,
    required this.methodologyHash,
  });

  final String caseVersionId;
  final String overallStatus;
  final int verifiedCount;
  final int totalCount;
  final List<QualityChecklistItemModel> items;
  final String methodologyHash;

  bool get isFullyAudited => verifiedCount == totalCount && totalCount > 0;

  factory CaseQualityChecklistModel.fromJson(Map<String, dynamic> json) =>
      CaseQualityChecklistModel(
        caseVersionId: json['case_version_id'] as String? ?? '',
        overallStatus: json['overall_status'] as String? ?? '',
        verifiedCount: (json['verified_count'] as num?)?.toInt() ?? 0,
        totalCount: (json['total_count'] as num?)?.toInt() ?? 0,
        items: (json['items'] as List<dynamic>? ?? const [])
            .map((e) => QualityChecklistItemModel.fromJson(e as Map<String, dynamic>))
            .toList(),
        methodologyHash: json['methodology_hash'] as String? ?? '',
      );

  Map<String, dynamic> toJson() => {
    'case_version_id': caseVersionId,
    'overall_status': overallStatus,
    'verified_count': verifiedCount,
    'total_count': totalCount,
    'items': items.map((i) => i.toJson()).toList(),
    'methodology_hash': methodologyHash,
  };
}
