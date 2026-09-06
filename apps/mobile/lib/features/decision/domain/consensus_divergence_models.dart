import 'package:flutter/foundation.dart';

enum DivergenceCategory {
  broadConsensus('BROAD_CONSENSUS'),
  bipolarDivergence('BIPOLAR_DIVERGENCE'),
  fragmentedPlurality('FRAGMENTED_PLURALITY'),
  leaningMajority('LEANING_MAJORITY');

  const DivergenceCategory(this.wireValue);
  final String wireValue;

  static DivergenceCategory fromString(String value) {
    return DivergenceCategory.values.firstWhere(
      (e) => e.wireValue == value,
      orElse: () => DivergenceCategory.leaningMajority,
    );
  }
}

@immutable
class ConsensusDivergenceModel {
  const ConsensusDivergenceModel({
    required this.caseVersionId,
    required this.distribution,
    required this.classification,
    required this.leadingShare,
    required this.marginOfDivergence,
    required this.labelTr,
    required this.labelEn,
    required this.descriptionTr,
    required this.descriptionEn,
  });

  final String caseVersionId;
  final Map<String, double> distribution;
  final DivergenceCategory classification;
  final double leadingShare;
  final double marginOfDivergence;
  final String labelTr;
  final String labelEn;
  final String descriptionTr;
  final String descriptionEn;

  factory ConsensusDivergenceModel.fromJson(Map<String, dynamic> json) {
    final rawDist = json['distribution'] as Map<String, dynamic>? ?? {};
    final dist = rawDist.map(
      (key, value) => MapEntry(key, (value as num).toDouble()),
    );

    return ConsensusDivergenceModel(
      caseVersionId: json['case_version_id'] as String? ?? '',
      distribution: dist,
      classification: DivergenceCategory.fromString(
        json['classification'] as String? ?? '',
      ),
      leadingShare: (json['leading_share'] as num?)?.toDouble() ?? 0.0,
      marginOfDivergence: (json['margin_of_divergence'] as num?)?.toDouble() ?? 0.0,
      labelTr: json['label_tr'] as String? ?? '',
      labelEn: json['label_en'] as String? ?? '',
      descriptionTr: json['description_tr'] as String? ?? '',
      descriptionEn: json['description_en'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'case_version_id': caseVersionId,
      'distribution': distribution,
      'classification': classification.wireValue,
      'leading_share': leadingShare,
      'margin_of_divergence': marginOfDivergence,
      'label_tr': labelTr,
      'label_en': labelEn,
      'description_tr': descriptionTr,
      'description_en': descriptionEn,
    };
  }
}
