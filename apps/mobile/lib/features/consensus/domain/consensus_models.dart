import 'package:flutter/foundation.dart';

@immutable
class ConsensusParticipation {
  const ConsensusParticipation({
    required this.stanceCode,
    required this.reasonTagCodes,
    required this.contributionClass,
    required this.participatedAt,
  });

  final String stanceCode;
  final List<String> reasonTagCodes;
  final String contributionClass;
  final DateTime participatedAt;
}

@immutable
class ConsensusAggregate {
  const ConsensusAggregate({
    required this.sampleSize,
    required this.stanceDistribution,
    required this.reasonPatternDistribution,
    required this.contributionClass,
    required this.methodologyVersion,
    required this.generatedAt,
    required this.provenanceNote,
  });

  final int sampleSize;
  final Map<String, double> stanceDistribution;
  final Map<String, double> reasonPatternDistribution;
  final String contributionClass;
  final String methodologyVersion;
  final DateTime generatedAt;
  final String provenanceNote;
}

@immutable
class ConsensusCard {
  const ConsensusCard({
    required this.id,
    required this.versionId,
    required this.caseVersionId,
    required this.proposition,
    required this.stanceCodes,
    required this.reasonTagCodes,
    required this.maxReasonTags,
    required this.methodologyVersion,
    required this.participationState,
    required this.contributionClass,
    this.participation,
    this.aggregate,
  });

  final String id;
  final String versionId;
  final String caseVersionId;
  final String proposition;
  final List<String> stanceCodes;
  final List<String> reasonTagCodes;
  final int maxReasonTags;
  final String methodologyVersion;
  final String participationState;
  final String contributionClass;
  final ConsensusParticipation? participation;
  final ConsensusAggregate? aggregate;

  bool get participated => participation != null && aggregate != null;

  ConsensusCard copyWith({
    ConsensusParticipation? participation,
    ConsensusAggregate? aggregate,
    String? participationState,
  }) {
    return ConsensusCard(
      id: id,
      versionId: versionId,
      caseVersionId: caseVersionId,
      proposition: proposition,
      stanceCodes: stanceCodes,
      reasonTagCodes: reasonTagCodes,
      maxReasonTags: maxReasonTags,
      methodologyVersion: methodologyVersion,
      participationState: participationState ?? this.participationState,
      contributionClass: contributionClass,
      participation: participation ?? this.participation,
      aggregate: aggregate ?? this.aggregate,
    );
  }
}
