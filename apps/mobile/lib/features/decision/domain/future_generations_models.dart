import 'package:flutter/foundation.dart';

enum TimeHorizonModel {
  horizon5Years,
  horizon20Years,
  horizon50Years,
  horizon100Years,
}

@immutable
class HorizonProjectionItemModel {
  const HorizonProjectionItemModel({
    required this.horizon,
    required this.impactScore,
    required this.summary,
  });

  final TimeHorizonModel horizon;
  final double impactScore;
  final String summary;
}

@immutable
class FutureGenerationsModel {
  const FutureGenerationsModel({
    required this.caseVersionId,
    required this.optionCode,
    required this.netIntergenerationalScore,
    required this.projections,
  });

  final String caseVersionId;
  final String optionCode;
  final double netIntergenerationalScore;
  final List<HorizonProjectionItemModel> projections;
}
