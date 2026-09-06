import 'package:flutter/foundation.dart';

enum ImpactEvidenceTypeModel {
  officialGazetteDecree,
  auditExpenditureReceipt,
  sensorTelemetryData,
  thirdPartyAcademicStudy,
}

enum EvidenceVerificationStatusModel {
  pendingAudit,
  verifiedAuthentic,
  challengedOrInsufficient,
}

@immutable
class ImpactEvidenceModel {
  const ImpactEvidenceModel({
    required this.evidenceId,
    required this.actionId,
    required this.evidenceType,
    required this.evidenceTitle,
    required this.sourceUrl,
    required this.sha256Digest,
    required this.verificationStatus,
  });

  final String evidenceId;
  final String actionId;
  final ImpactEvidenceTypeModel evidenceType;
  final String evidenceTitle;
  final String sourceUrl;
  final String sha256Digest;
  final EvidenceVerificationStatusModel verificationStatus;
}
