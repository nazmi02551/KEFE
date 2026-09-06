import 'package:flutter/foundation.dart';

enum ActionFollowThroughStatus {
  proposed,
  inProgress,
  verifiedComplete,
  stalled;

  static ActionFollowThroughStatus fromString(String val) =>
      switch (val.toUpperCase()) {
        'IN_PROGRESS' => inProgress,
        'VERIFIED_COMPLETE' => verifiedComplete,
        'STALLED' => stalled,
        _ => proposed,
      };

  String get serializedName => switch (this) {
    proposed => 'PROPOSED',
    inProgress => 'IN_PROGRESS',
    verifiedComplete => 'VERIFIED_COMPLETE',
    stalled => 'STALLED',
  };
}

@immutable
class ActionFollowThroughItem {
  const ActionFollowThroughItem({
    required this.id,
    required this.caseVersionId,
    required this.title,
    required this.description,
    required this.status,
    required this.progressPercentage,
    required this.createdAt,
    this.targetCompletionDate,
    this.evidenceSummary,
    this.evidenceUrl,
  });

  final String id;
  final String caseVersionId;
  final String title;
  final String description;
  final ActionFollowThroughStatus status;
  final int progressPercentage;
  final DateTime createdAt;
  final DateTime? targetCompletionDate;
  final String? evidenceSummary;
  final String? evidenceUrl;

  factory ActionFollowThroughItem.fromJson(Map<String, dynamic> json) =>
      ActionFollowThroughItem(
        id: json['action_id'] as String? ?? '',
        caseVersionId: json['case_version_id'] as String? ?? '',
        title: json['title'] as String? ?? '',
        description: json['description'] as String? ?? '',
        status: ActionFollowThroughStatus.fromString(
          json['status'] as String? ?? '',
        ),
        progressPercentage: (json['progress_percentage'] as num?)?.toInt() ?? 0,
        createdAt:
            DateTime.tryParse(json['created_at'] as String? ?? '')?.toUtc() ??
            DateTime.now().toUtc(),
        targetCompletionDate: json['target_completion_date'] != null
            ? DateTime.tryParse(
                json['target_completion_date'] as String,
              )?.toUtc()
            : null,
        evidenceSummary: json['evidence_summary'] as String?,
        evidenceUrl: json['evidence_url'] as String?,
      );

  Map<String, dynamic> toJson() => {
    'action_id': id,
    'case_version_id': caseVersionId,
    'title': title,
    'description': description,
    'status': status.serializedName,
    'progress_percentage': progressPercentage,
    'created_at': createdAt.toIso8601String(),
    if (targetCompletionDate != null)
      'target_completion_date': targetCompletionDate!.toIso8601String(),
    if (evidenceSummary != null) 'evidence_summary': evidenceSummary,
    if (evidenceUrl != null) 'evidence_url': evidenceUrl,
  };
}
