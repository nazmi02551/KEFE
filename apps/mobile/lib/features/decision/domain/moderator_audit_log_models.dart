import 'package:flutter/foundation.dart';

enum ModerationActionTypeModel {
  reasonRemovedPolicyBreach,
  flagDismissedValid,
  caseVersionFreeze,
  userWarningIssued,
}

@immutable
class ModeratorAuditLogModel {
  const ModeratorAuditLogModel({
    required this.auditId,
    required this.targetResourceId,
    required this.moderatorId,
    required this.actionType,
    required this.policyRuleReference,
    required this.justificationText,
    required this.actionHash,
    required this.createdAtUtc,
  });

  final String auditId;
  final String targetResourceId;
  final String moderatorId;
  final ModerationActionTypeModel actionType;
  final String policyRuleReference;
  final String justificationText;
  final String actionHash;
  final String createdAtUtc;
}
