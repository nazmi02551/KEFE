import 'package:flutter/foundation.dart';

enum NormativePhilosophyModel {
  utilitarianMaxWelfare,
  deontologicalCategoricalRights,
  rawlsianMaximinEquity,
  virtueEthicsCharacter,
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
  final NormativePhilosophyModel dominantPhilosophy;
}

@immutable
class CaseNormativeModelResultModel {
  const CaseNormativeModelResultModel({
    required this.caseVersionId,
    required this.evaluations,
  });

  final String caseVersionId;
  final List<OptionNormativeEvaluationModel> evaluations;
}
