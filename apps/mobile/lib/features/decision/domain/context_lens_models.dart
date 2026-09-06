import 'package:flutter/foundation.dart';

enum LensPillarTypeModel {
  legalFramework,
  historicalContext,
  scientificData,
  comparativePractice,
}

@immutable
class ContextLensPillarModel {
  const ContextLensPillarModel({
    required this.pillarType,
    required this.title,
    required this.content,
    required this.sourceCitation,
    this.sourceUrl,
  });

  final LensPillarTypeModel pillarType;
  final String title;
  final String content;
  final String sourceCitation;
  final String? sourceUrl;
}

@immutable
class ContextLensModel {
  const ContextLensModel({
    required this.caseVersionId,
    required this.pillars,
  });

  final String caseVersionId;
  final List<ContextLensPillarModel> pillars;
}
