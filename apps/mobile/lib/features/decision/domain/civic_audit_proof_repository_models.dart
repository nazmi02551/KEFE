import 'package:flutter/foundation.dart';

enum AuditVerificationStatusModel {
  peerAttestedCorroborated,
  openEvidentiaryChallenge,
  pendingWitnessConfirmation,
}

@immutable
class CivicAuditReportModel {
  const CivicAuditReportModel({
    required this.reportId,
    required this.investigationTitle,
    required this.verificationStatus,
    required this.peerAttestationSignaturesCount,
    required this.evidentiaryRigorScore,
    required this.contentHashDigest,
  });

  final String reportId;
  final String investigationTitle;
  final AuditVerificationStatusModel verificationStatus;
  final int peerAttestationSignaturesCount;
  final double evidentiaryRigorScore;
  final String contentHashDigest;
}
