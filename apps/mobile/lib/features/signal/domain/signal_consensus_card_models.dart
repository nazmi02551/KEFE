import 'package:flutter/foundation.dart';

enum SignalConfidenceTierModel {
  gold,
  silver,
  bronze,
}

@immutable
class SignalConsensusCardModel {
  const SignalConsensusCardModel({
    required this.signalId,
    required this.caseVersionId,
    required this.caseTitle,
    required this.consensusStatement,
    required this.agreementPercentage,
    required this.sampleSize,
    required this.confidenceTier,
    required this.certifiedAt,
    this.isProvisional = false,
  });

  final String signalId;
  final String caseVersionId;
  final String caseTitle;
  final String consensusStatement;
  final double agreementPercentage;
  final int sampleSize;
  final SignalConfidenceTierModel confidenceTier;
  final DateTime certifiedAt;
  final bool isProvisional;

  factory SignalConsensusCardModel.fromJson(Map<String, dynamic> json) {
    final tierStr =
        (json['confidence_tier'] as String? ?? 'BRONZE').toUpperCase();
    final tier = switch (tierStr) {
      'GOLD' => SignalConfidenceTierModel.gold,
      'SILVER' => SignalConfidenceTierModel.silver,
      _ => SignalConfidenceTierModel.bronze,
    };
    final rawStatement = json['consensus_statement'] as String;
    // Strip [PROVISIONAL] prefix from display — the isProvisional flag is set separately
    final displayStatement = rawStatement.startsWith('[PROVISIONAL]')
        ? rawStatement
            .replaceFirst(RegExp(r'^\[PROVISIONAL\]\s*'), '')
            .trim()
        : rawStatement;

    return SignalConsensusCardModel(
      signalId: json['signal_id'] as String,
      caseVersionId: json['case_version_id'] as String,
      caseTitle: json['case_title'] as String,
      consensusStatement: displayStatement,
      agreementPercentage: (json['agreement_percentage'] as num).toDouble(),
      sampleSize: (json['sample_size'] as num).toInt(),
      confidenceTier: tier,
      certifiedAt:
          DateTime.tryParse(json['certified_at'] as String? ?? '')?.toUtc() ??
          DateTime.now().toUtc(),
      isProvisional: json['is_provisional'] as bool? ??
          rawStatement.contains('[PROVISIONAL]'),
    );
  }

  Map<String, dynamic> toJson() => {
    'signal_id': signalId,
    'case_version_id': caseVersionId,
    'case_title': caseTitle,
    'consensus_statement': consensusStatement,
    'agreement_percentage': agreementPercentage,
    'sample_size': sampleSize,
    'confidence_tier': confidenceTier.name.toUpperCase(),
    'certified_at': certifiedAt.toIso8601String(),
    'is_provisional': isProvisional,
  };
}
