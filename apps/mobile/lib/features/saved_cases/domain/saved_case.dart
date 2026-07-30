import 'package:flutter/foundation.dart';

import '../../decision/domain/decision_models.dart';

@immutable
class SavedCase {
  const SavedCase({
    required this.caseId,
    required this.caseVersionId,
    required this.title,
    required this.summary,
    required this.domain,
    required this.format,
    required this.risk,
    required this.savedAt,
  });

  factory SavedCase.fromSummary(
    DecisionCaseSummary summary, {
    DateTime? savedAt,
  }) {
    return SavedCase(
      caseId: summary.id,
      caseVersionId: summary.versionId,
      title: summary.title,
      summary: summary.summary,
      domain: summary.domain,
      format: summary.format,
      risk: summary.risk,
      savedAt: savedAt ?? DateTime.now().toUtc(),
    );
  }

  factory SavedCase.fromJson(Map<String, Object?> json) {
    return SavedCase(
      caseId: json['case_id']?.toString() ?? '',
      caseVersionId: json['case_version_id']?.toString() ?? '',
      title: json['title']?.toString() ?? '',
      summary: json['summary']?.toString() ?? '',
      domain: json['domain']?.toString() ?? '',
      format: json['format']?.toString() ?? '',
      risk: json['risk']?.toString() ?? '',
      savedAt:
          DateTime.tryParse(json['saved_at']?.toString() ?? '')?.toUtc() ??
          DateTime.fromMillisecondsSinceEpoch(0, isUtc: true),
    );
  }

  final String caseId;
  final String caseVersionId;
  final String title;
  final String summary;
  final String domain;
  final String format;
  final String risk;
  final DateTime savedAt;

  bool get isValid =>
      caseId.isNotEmpty &&
      caseVersionId.isNotEmpty &&
      title.isNotEmpty &&
      domain.isNotEmpty;

  Map<String, Object?> toJson() => {
    'case_id': caseId,
    'case_version_id': caseVersionId,
    'title': title,
    'summary': summary,
    'domain': domain,
    'format': format,
    'risk': risk,
    'saved_at': savedAt.toIso8601String(),
  };
}
