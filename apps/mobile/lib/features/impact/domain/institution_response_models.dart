import 'package:flutter/foundation.dart';

enum InstitutionResponseType {
  acknowledge,
  commitment,
  policyChange,
  factualClarification,
  declineWithReason;

  static InstitutionResponseType fromString(String val) =>
      switch (val.toUpperCase()) {
        'POLICY_CHANGE' => policyChange,
        'COMMITMENT' => commitment,
        'FACTUAL_CLARIFICATION' => factualClarification,
        'DECLINE_WITH_REASON' => declineWithReason,
        _ => acknowledge,
      };

  String get serializedName => switch (this) {
    policyChange => 'POLICY_CHANGE',
    commitment => 'COMMITMENT',
    factualClarification => 'FACTUAL_CLARIFICATION',
    declineWithReason => 'DECLINE_WITH_REASON',
    acknowledge => 'ACKNOWLEDGE',
  };
}

enum AuthorityVerificationStatus {
  verified,
  pendingVerification,
  rejected;

  static AuthorityVerificationStatus fromString(String val) =>
      switch (val.toUpperCase()) {
        'VERIFIED' => verified,
        'PENDING_VERIFICATION' => pendingVerification,
        'REJECTED' => rejected,
        _ => pendingVerification,
      };

  String get serializedName => switch (this) {
    verified => 'VERIFIED',
    pendingVerification => 'PENDING_VERIFICATION',
    rejected => 'REJECTED',
  };
}

@immutable
class InstitutionResponseItem {
  const InstitutionResponseItem({
    required this.id,
    required this.caseVersionId,
    required this.institutionName,
    required this.authorityRole,
    required this.verificationStatus,
    required this.responseType,
    required this.statement,
    required this.publishedAt,
    this.milestoneDate,
  });

  final String id;
  final String caseVersionId;
  final String institutionName;
  final String authorityRole;
  final AuthorityVerificationStatus verificationStatus;
  final InstitutionResponseType responseType;
  final String statement;
  final DateTime publishedAt;
  final DateTime? milestoneDate;

  factory InstitutionResponseItem.fromJson(Map<String, dynamic> json) =>
      InstitutionResponseItem(
        id: json['response_id'] as String? ?? '',
        caseVersionId: json['case_version_id'] as String? ?? '',
        institutionName: json['institution_name'] as String? ?? '',
        authorityRole: json['authority_role'] as String? ?? '',
        verificationStatus: AuthorityVerificationStatus.fromString(
          json['verification_status'] as String? ?? '',
        ),
        responseType: InstitutionResponseType.fromString(
          json['response_type'] as String? ?? '',
        ),
        statement: json['statement'] as String? ?? '',
        publishedAt:
            DateTime.tryParse(json['published_at'] as String? ?? '')?.toUtc() ??
            DateTime.now().toUtc(),
        milestoneDate: json['milestone_date'] != null
            ? DateTime.tryParse(json['milestone_date'] as String)?.toUtc()
            : null,
      );

  Map<String, dynamic> toJson() => {
    'response_id': id,
    'case_version_id': caseVersionId,
    'institution_name': institutionName,
    'authority_role': authorityRole,
    'verification_status': verificationStatus.serializedName,
    'response_type': responseType.serializedName,
    'statement': statement,
    'published_at': publishedAt.toIso8601String(),
    if (milestoneDate != null)
      'milestone_date': milestoneDate!.toIso8601String(),
  };
}
