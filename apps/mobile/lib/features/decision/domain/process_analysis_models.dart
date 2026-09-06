class ProcessStageModel {
  const ProcessStageModel({
    required this.stageKey,
    required this.stageTitle,
    required this.isCompleted,
    required this.durationDays,
    required this.hasPublicInput,
    this.notes = '',
  });

  factory ProcessStageModel.fromJson(Map<String, dynamic> json) {
    return ProcessStageModel(
      stageKey: json['stage_key'] as String? ?? '',
      stageTitle: json['stage_title'] as String? ?? '',
      isCompleted: json['is_completed'] as bool? ?? false,
      durationDays: (json['duration_days'] as num?)?.toInt() ?? 0,
      hasPublicInput: json['has_public_input'] as bool? ?? false,
      notes: json['notes'] as String? ?? '',
    );
  }

  final String stageKey;
  final String stageTitle;
  final bool isCompleted;
  final int durationDays;
  final bool hasPublicInput;
  final String notes;

  Map<String, dynamic> toJson() => {
    'stage_key': stageKey,
    'stage_title': stageTitle,
    'is_completed': isCompleted,
    'duration_days': durationDays,
    'has_public_input': hasPublicInput,
    'notes': notes,
  };
}

class ProcessAnalysisModel {
  const ProcessAnalysisModel({
    required this.analysisId,
    required this.caseVersionId,
    required this.currentStage,
    required this.proceduralIntegrityScore,
    required this.transparencyLevel,
    required this.publicParticipationStatus,
    required this.oversightBody,
    required this.stages,
    this.proceduralBottleneck,
  });

  factory ProcessAnalysisModel.fromJson(Map<String, dynamic> json) {
    final stagesRaw = json['stages'] as List<dynamic>? ?? const [];
    return ProcessAnalysisModel(
      analysisId: json['analysis_id'] as String? ?? '',
      caseVersionId: json['case_version_id'] as String? ?? '',
      currentStage: json['current_stage'] as String? ?? 'DECISION_ENACTED',
      proceduralIntegrityScore: (json['procedural_integrity_score'] as num?)?.toDouble() ?? 0.0,
      transparencyLevel: json['transparency_level'] as String? ?? 'MODERATE',
      publicParticipationStatus: json['public_participation_status'] as String? ?? 'OPEN_CONSULTATION',
      oversightBody: json['oversight_body'] as String? ?? '',
      proceduralBottleneck: json['procedural_bottleneck'] as String?,
      stages: stagesRaw
          .whereType<Map<String, dynamic>>()
          .map(ProcessStageModel.fromJson)
          .toList(growable: false),
    );
  }

  final String analysisId;
  final String caseVersionId;
  final String currentStage;
  final double proceduralIntegrityScore;
  final String transparencyLevel;
  final String publicParticipationStatus;
  final String oversightBody;
  final String? proceduralBottleneck;
  final List<ProcessStageModel> stages;

  Map<String, dynamic> toJson() => {
    'analysis_id': analysisId,
    'case_version_id': caseVersionId,
    'current_stage': currentStage,
    'procedural_integrity_score': proceduralIntegrityScore,
    'transparency_level': transparencyLevel,
    'public_participation_status': publicParticipationStatus,
    'oversight_body': oversightBody,
    'procedural_bottleneck': proceduralBottleneck,
    'stages': stages.map((s) => s.toJson()).toList(),
  };
}
