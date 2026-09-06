import 'package:flutter/foundation.dart';

enum AiAuditStatusModel {
  auditVerifiedGrounded,
  potentialHallucinationFlag,
  asymmetricBiasSkew,
}

@immutable
class AiAuditModel {
  const AiAuditModel({
    required this.auditId,
    required this.targetArtifactId,
    required this.status,
    required this.groundingConfidenceScore,
    required this.biasAsymmetryIndex,
    required this.auditFindingsSummary,
  });

  final String auditId;
  final String targetArtifactId;
  final AiAuditStatusModel status;
  final double groundingConfidenceScore;
  final double biasAsymmetryIndex;
  final String auditFindingsSummary;
}
