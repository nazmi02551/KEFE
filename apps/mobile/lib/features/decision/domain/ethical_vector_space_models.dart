import 'package:flutter/foundation.dart';

enum DominantMoralAttractorModel {
  utilitarianWelfare,
  deontologicalRights,
  communitarianSolidarity,
  intergenerationalCare,
}

@immutable
class EthicalVectorSpaceModel {
  const EthicalVectorSpaceModel({
    required this.caseVersionId,
    required this.utilitarianWeight,
    required this.deontologicalWeight,
    required this.communitarianWeight,
    required this.intergenerationalWeight,
    required this.dominantAttractor,
  });

  final String caseVersionId;
  final double utilitarianWeight;
  final double deontologicalWeight;
  final double communitarianWeight;
  final double intergenerationalWeight;
  final DominantMoralAttractorModel dominantAttractor;
}
