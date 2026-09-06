class SignalSnapshotModel {
  const SignalSnapshotModel({
    required this.snapshotId,
    required this.methodologyVersion,
    required this.methodologyName,
    required this.sampleSize,
    required this.confidenceScore,
    required this.consensusDistribution,
    required this.calculatedAt,
    this.parentSnapshotHash,
    required this.snapshotHash,
  });

  final String snapshotId;
  final String methodologyVersion;
  final String methodologyName;
  final int sampleSize;
  final double confidenceScore;
  final Map<String, double> consensusDistribution;
  final String calculatedAt;
  final String? parentSnapshotHash;
  final String snapshotHash;

  factory SignalSnapshotModel.fromJson(Map<String, dynamic> json) {
    final distRaw = json['consensus_distribution'] as Map<String, dynamic>;
    final dist = distRaw.map((k, v) => MapEntry(k, (v as num).toDouble()));

    return SignalSnapshotModel(
      snapshotId: json['snapshot_id'] as String,
      methodologyVersion: json['methodology_version'] as String,
      methodologyName: json['methodology_name'] as String,
      sampleSize: json['sample_size'] as int,
      confidenceScore: (json['confidence_score'] as num).toDouble(),
      consensusDistribution: dist,
      calculatedAt: json['calculated_at'] as String,
      parentSnapshotHash: json['parent_snapshot_hash'] as String?,
      snapshotHash: json['snapshot_hash'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'snapshot_id': snapshotId,
    'methodology_version': methodologyVersion,
    'methodology_name': methodologyName,
    'sample_size': sampleSize,
    'confidence_score': confidenceScore,
    'consensus_distribution': consensusDistribution,
    'calculated_at': calculatedAt,
    'parent_snapshot_hash': parentSnapshotHash,
    'snapshot_hash': snapshotHash,
  };
}

class MethodologyDeltaModel {
  const MethodologyDeltaModel({
    required this.fromVersion,
    required this.toVersion,
    required this.distributionShift,
    required this.confidenceDelta,
    required this.notes,
  });

  final String fromVersion;
  final String toVersion;
  final double distributionShift;
  final double confidenceDelta;
  final String notes;

  factory MethodologyDeltaModel.fromJson(Map<String, dynamic> json) {
    return MethodologyDeltaModel(
      fromVersion: json['from_version'] as String,
      toVersion: json['to_version'] as String,
      distributionShift: (json['distribution_shift'] as num).toDouble(),
      confidenceDelta: (json['confidence_delta'] as num).toDouble(),
      notes: json['notes'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'from_version': fromVersion,
    'to_version': toVersion,
    'distribution_shift': distributionShift,
    'confidence_delta': confidenceDelta,
    'notes': notes,
  };
}

class SignalVersioningReportModel {
  const SignalVersioningReportModel({
    required this.signalId,
    required this.caseVersionId,
    required this.currentVersion,
    required this.currentMethodologyHash,
    required this.snapshots,
    this.latestDelta,
    required this.auditChainValid,
    required this.certifiedAt,
  });

  final String signalId;
  final String caseVersionId;
  final String currentVersion;
  final String currentMethodologyHash;
  final List<SignalSnapshotModel> snapshots;
  final MethodologyDeltaModel? latestDelta;
  final bool auditChainValid;
  final String certifiedAt;

  factory SignalVersioningReportModel.fromJson(Map<String, dynamic> json) {
    return SignalVersioningReportModel(
      signalId: json['signal_id'] as String,
      caseVersionId: json['case_version_id'] as String,
      currentVersion: json['current_version'] as String,
      currentMethodologyHash: json['current_methodology_hash'] as String,
      snapshots: (json['snapshots'] as List<dynamic>)
          .map((e) => SignalSnapshotModel.fromJson(e as Map<String, dynamic>))
          .toList(),
      latestDelta: json['latest_delta'] != null
          ? MethodologyDeltaModel.fromJson(json['latest_delta'] as Map<String, dynamic>)
          : null,
      auditChainValid: json['audit_chain_valid'] as bool,
      certifiedAt: json['certified_at'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'signal_id': signalId,
    'case_version_id': caseVersionId,
    'current_version': currentVersion,
    'current_methodology_hash': currentMethodologyHash,
    'snapshots': snapshots.map((e) => e.toJson()).toList(),
    'latest_delta': latestDelta?.toJson(),
    'audit_chain_valid': auditChainValid,
    'certified_at': certifiedAt,
  };
}
