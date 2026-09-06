enum TargetTypeModel {
  municipalGovernment,
  ministryDepartment,
  regulatoryBody,
  publicUtility,
  corporateEntity,
  civicOmbudsman;

  static TargetTypeModel fromString(String value) {
    return switch (value.toUpperCase()) {
      'MUNICIPAL_GOVERNMENT' => TargetTypeModel.municipalGovernment,
      'MINISTRY_DEPARTMENT' => TargetTypeModel.ministryDepartment,
      'REGULATORY_BODY' => TargetTypeModel.regulatoryBody,
      'PUBLIC_UTILITY' => TargetTypeModel.publicUtility,
      'CORPORATE_ENTITY' => TargetTypeModel.corporateEntity,
      'CIVIC_OMBUDSMAN' => TargetTypeModel.civicOmbudsman,
      _ => TargetTypeModel.municipalGovernment,
    };
  }

  String toJsonValue() {
    return switch (this) {
      TargetTypeModel.municipalGovernment => 'MUNICIPAL_GOVERNMENT',
      TargetTypeModel.ministryDepartment => 'MINISTRY_DEPARTMENT',
      TargetTypeModel.regulatoryBody => 'REGULATORY_BODY',
      TargetTypeModel.publicUtility => 'PUBLIC_UTILITY',
      TargetTypeModel.corporateEntity => 'CORPORATE_ENTITY',
      TargetTypeModel.civicOmbudsman => 'CIVIC_OMBUDSMAN',
    };
  }
}

enum DispatchStatusModel {
  proposedTarget,
  verifiedTarget,
  dispatched,
  acknowledged,
  actionPledged,
  declinedJurisdiction;

  static DispatchStatusModel fromString(String value) {
    return switch (value.toUpperCase()) {
      'PROPOSED_TARGET' => DispatchStatusModel.proposedTarget,
      'VERIFIED_TARGET' => DispatchStatusModel.verifiedTarget,
      'DISPATCHED' => DispatchStatusModel.dispatched,
      'ACKNOWLEDGED' => DispatchStatusModel.acknowledged,
      'ACTION_PLEDGED' => DispatchStatusModel.actionPledged,
      'DECLINED_JURISDICTION' => DispatchStatusModel.declinedJurisdiction,
      _ => DispatchStatusModel.proposedTarget,
    };
  }

  String toJsonValue() {
    return switch (this) {
      DispatchStatusModel.proposedTarget => 'PROPOSED_TARGET',
      DispatchStatusModel.verifiedTarget => 'VERIFIED_TARGET',
      DispatchStatusModel.dispatched => 'DISPATCHED',
      DispatchStatusModel.acknowledged => 'ACKNOWLEDGED',
      DispatchStatusModel.actionPledged => 'ACTION_PLEDGED',
      DispatchStatusModel.declinedJurisdiction => 'DECLINED_JURISDICTION',
    };
  }
}

class SignalTargetItemModel {
  const SignalTargetItemModel({
    required this.targetId,
    required this.targetName,
    required this.targetType,
    required this.jurisdictionLevel,
    required this.officialContactChannel,
    required this.dispatchStatus,
    required this.responseDueDays,
    this.dispatchedAt,
    this.acknowledgedAt,
  });

  final String targetId;
  final String targetName;
  final TargetTypeModel targetType;
  final String jurisdictionLevel;
  final String officialContactChannel;
  final DispatchStatusModel dispatchStatus;
  final int responseDueDays;
  final String? dispatchedAt;
  final String? acknowledgedAt;

  factory SignalTargetItemModel.fromJson(Map<String, dynamic> json) {
    return SignalTargetItemModel(
      targetId: json['target_id'] as String,
      targetName: json['target_name'] as String,
      targetType: TargetTypeModel.fromString(json['target_type'] as String),
      jurisdictionLevel: json['jurisdiction_level'] as String,
      officialContactChannel: json['official_contact_channel'] as String,
      dispatchStatus: DispatchStatusModel.fromString(json['dispatch_status'] as String),
      responseDueDays: json['response_due_days'] as int,
      dispatchedAt: json['dispatched_at'] as String?,
      acknowledgedAt: json['acknowledged_at'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'target_id': targetId,
    'target_name': targetName,
    'target_type': targetType.toJsonValue(),
    'jurisdiction_level': jurisdictionLevel,
    'official_contact_channel': officialContactChannel,
    'dispatch_status': dispatchStatus.toJsonValue(),
    'response_due_days': responseDueDays,
    'dispatched_at': dispatchedAt,
    'acknowledged_at': acknowledgedAt,
  };
}

class SignalTargetRegistryReportModel {
  const SignalTargetRegistryReportModel({
    required this.signalId,
    required this.caseVersionId,
    required this.primaryTargetId,
    required this.targets,
    required this.certifiedAt,
    required this.registryProofHash,
  });

  final String signalId;
  final String caseVersionId;
  final String primaryTargetId;
  final List<SignalTargetItemModel> targets;
  final String certifiedAt;
  final String registryProofHash;

  factory SignalTargetRegistryReportModel.fromJson(Map<String, dynamic> json) {
    return SignalTargetRegistryReportModel(
      signalId: json['signal_id'] as String,
      caseVersionId: json['case_version_id'] as String,
      primaryTargetId: json['primary_target_id'] as String,
      targets: (json['targets'] as List<dynamic>)
          .map((e) => SignalTargetItemModel.fromJson(e as Map<String, dynamic>))
          .toList(),
      certifiedAt: json['certified_at'] as String,
      registryProofHash: json['registry_proof_hash'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'signal_id': signalId,
    'case_version_id': caseVersionId,
    'primary_target_id': primaryTargetId,
    'targets': targets.map((e) => e.toJson()).toList(),
    'certified_at': certifiedAt,
    'registry_proof_hash': registryProofHash,
  };
}
