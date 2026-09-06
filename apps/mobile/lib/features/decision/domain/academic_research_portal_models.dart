import 'package:flutter/foundation.dart';

enum ResearchCorpusTypeModel {
  deliberativePolarizationDataset,
  ethicalTradeOffCorpus,
  argumentGraphTopology,
  policyOutcomeBenchmark,
}

@immutable
class AcademicResearchDatasetModel {
  const AcademicResearchDatasetModel({
    required this.datasetId,
    required this.datasetTitle,
    required this.corpusType,
    required this.recordCount,
    required this.differentialPrivacyEpsilon,
    required this.doiIdentifier,
  });

  final String datasetId;
  final String datasetTitle;
  final ResearchCorpusTypeModel corpusType;
  final int recordCount;
  final double differentialPrivacyEpsilon;
  final String doiIdentifier;
}
