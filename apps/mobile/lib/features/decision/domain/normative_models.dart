import 'package:flutter/foundation.dart';

enum NormativePhilosophyType {
  utilitarianMaxWelfare('UTILITARIAN_MAX_WELFARE'),
  deontologicalCategoricalRights('DEONTOLOGICAL_CATEGORICAL_RIGHTS'),
  rawlsianMaximinEquity('RAWLSIAN_MAXIMIN_EQUITY'),
  virtueEthicsCharacter('VIRTUE_ETHICS_CHARACTER');

  const NormativePhilosophyType(this.wireValue);
  final String wireValue;

  static NormativePhilosophyType fromString(String value) {
    return NormativePhilosophyType.values.firstWhere(
      (e) => e.wireValue == value,
      orElse: () => NormativePhilosophyType.utilitarianMaxWelfare,
    );
  }
}

@immutable
class OptionNormativeEvaluationModel {
  const OptionNormativeEvaluationModel({
    required this.optionCode,
    required this.utilitarianScore,
    required this.deontologicalScore,
    required this.rawlsianScore,
    required this.virtueScore,
    required this.dominantPhilosophy,
  });

  final String optionCode;
  final double utilitarianScore;
  final double deontologicalScore;
  final double rawlsianScore;
  final double virtueScore;
  final NormativePhilosophyType dominantPhilosophy;

  factory OptionNormativeEvaluationModel.fromJson(Map<String, dynamic> json) {
    return OptionNormativeEvaluationModel(
      optionCode: json['option_code'] as String? ?? '',
      utilitarianScore: (json['utilitarian_score'] as num?)?.toDouble() ?? 0.0,
      deontologicalScore: (json['deontological_score'] as num?)?.toDouble() ?? 0.0,
      rawlsianScore: (json['rawlsian_score'] as num?)?.toDouble() ?? 0.0,
      virtueScore: (json['virtue_score'] as num?)?.toDouble() ?? 0.0,
      dominantPhilosophy: NormativePhilosophyType.fromString(
        json['dominant_philosophy'] as String? ?? '',
      ),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'option_code': optionCode,
      'utilitarian_score': utilitarianScore,
      'deontological_score': deontologicalScore,
      'rawlsian_score': rawlsianScore,
      'virtue_score': virtueScore,
      'dominant_philosophy': dominantPhilosophy.wireValue,
    };
  }
}

@immutable
class CaseNormativeModelsModel {
  const CaseNormativeModelsModel({
    required this.caseVersionId,
    required this.evaluations,
    required this.philosophiesExplainedTr,
    required this.philosophiesExplainedEn,
  });

  final String caseVersionId;
  final List<OptionNormativeEvaluationModel> evaluations;
  final Map<String, String> philosophiesExplainedTr;
  final Map<String, String> philosophiesExplainedEn;

  factory CaseNormativeModelsModel.fromJson(Map<String, dynamic> json) {
    final rawEvals = json['evaluations'] as List<dynamic>? ?? [];
    final evals = rawEvals
        .map((e) => OptionNormativeEvaluationModel.fromJson(e as Map<String, dynamic>))
        .toList();

    final trExpl = (json['philosophies_explained_tr'] as Map<String, dynamic>? ?? {})
        .map((k, v) => MapEntry(k, v.toString()));
    final enExpl = (json['philosophies_explained_en'] as Map<String, dynamic>? ?? {})
        .map((k, v) => MapEntry(k, v.toString()));

    return CaseNormativeModelsModel(
      caseVersionId: json['case_version_id'] as String? ?? '',
      evaluations: evals,
      philosophiesExplainedTr: trExpl,
      philosophiesExplainedEn: enExpl,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'case_version_id': caseVersionId,
      'evaluations': evaluations.map((e) => e.toJson()).toList(),
      'philosophies_explained_tr': philosophiesExplainedTr,
      'philosophies_explained_en': philosophiesExplainedEn,
    };
  }
}
