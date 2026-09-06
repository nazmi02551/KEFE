import 'package:flutter/foundation.dart';

enum SourcePluralityCategoryModel {
  academicScientific,
  officialGovernment,
  civicIndependent,
  mainstreamJournalism,
  technicalIndustry;

  static SourcePluralityCategoryModel fromString(String val) =>
      switch (val.toUpperCase()) {
        'ACADEMIC_SCIENTIFIC' => academicScientific,
        'OFFICIAL_GOVERNMENT' => officialGovernment,
        'CIVIC_INDEPENDENT' => civicIndependent,
        'MAINSTREAM_JOURNALISM' => mainstreamJournalism,
        'TECHNICAL_INDUSTRY' => technicalIndustry,
        _ => civicIndependent,
      };

  String get serializedName => switch (this) {
    academicScientific => 'ACADEMIC_SCIENTIFIC',
    officialGovernment => 'OFFICIAL_GOVERNMENT',
    civicIndependent => 'CIVIC_INDEPENDENT',
    mainstreamJournalism => 'MAINSTREAM_JOURNALISM',
    technicalIndustry => 'TECHNICAL_INDUSTRY',
  };
}

enum DiversityLevelModel {
  highDiversity,
  balancedDiversity,
  limitedDiversity;

  static DiversityLevelModel fromString(String val) =>
      switch (val.toUpperCase()) {
        'HIGH_DIVERSITY' => highDiversity,
        'BALANCED_DIVERSITY' => balancedDiversity,
        'LIMITED_DIVERSITY' => limitedDiversity,
        _ => balancedDiversity,
      };

  String get serializedName => switch (this) {
    highDiversity => 'HIGH_DIVERSITY',
    balancedDiversity => 'BALANCED_DIVERSITY',
    limitedDiversity => 'LIMITED_DIVERSITY',
  };
}

@immutable
class SourceCategoryBreakdownModel {
  const SourceCategoryBreakdownModel({
    required this.category,
    required this.count,
    required this.percentage,
  });

  final SourcePluralityCategoryModel category;
  final int count;
  final double percentage;

  factory SourceCategoryBreakdownModel.fromJson(Map<String, dynamic> json) =>
      SourceCategoryBreakdownModel(
        category: SourcePluralityCategoryModel.fromString(
          json['category'] as String? ?? '',
        ),
        count: (json['count'] as num?)?.toInt() ?? 0,
        percentage: (json['percentage'] as num?)?.toDouble() ?? 0.0,
      );

  Map<String, dynamic> toJson() => {
    'category': category.serializedName,
    'count': count,
    'percentage': percentage,
  };
}

@immutable
class SourceDiversityModel {
  const SourceDiversityModel({
    required this.caseVersionId,
    required this.totalSources,
    required this.diversityLevel,
    required this.breakdown,
  });

  final String caseVersionId;
  final int totalSources;
  final DiversityLevelModel diversityLevel;
  final List<SourceCategoryBreakdownModel> breakdown;

  factory SourceDiversityModel.fromJson(Map<String, dynamic> json) {
    final rawBreakdown =
        json['category_breakdown'] as List<dynamic>? ?? const [];
    return SourceDiversityModel(
      caseVersionId: json['case_version_id'] as String? ?? '',
      totalSources: (json['total_sources'] as num?)?.toInt() ?? 0,
      diversityLevel: DiversityLevelModel.fromString(
        json['diversity_level'] as String? ?? '',
      ),
      breakdown: rawBreakdown
          .map(
            (item) => SourceCategoryBreakdownModel.fromJson(
              item as Map<String, dynamic>,
            ),
          )
          .toList(growable: false),
    );
  }

  Map<String, dynamic> toJson() => {
    'case_version_id': caseVersionId,
    'total_sources': totalSources,
    'diversity_level': diversityLevel.serializedName,
    'category_breakdown': breakdown
        .map((b) => b.toJson())
        .toList(growable: false),
  };
}
