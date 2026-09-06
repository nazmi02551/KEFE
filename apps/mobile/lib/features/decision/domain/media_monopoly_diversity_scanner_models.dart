import 'package:flutter/foundation.dart';

enum MediaPluralismLevelModel {
  pluralisticIndependentDiverse,
  corporateConglomerateConcentration,
  stateControlledMonopolyAlert,
}

@immutable
class MediaDiversityModel {
  const MediaDiversityModel({
    required this.scannerId,
    required this.topicCluster,
    required this.pluralismLevel,
    required this.sourceDiversityIndex,
    required this.independentOutletsCount,
  });

  final String scannerId;
  final String topicCluster;
  final MediaPluralismLevelModel pluralismLevel;
  final double sourceDiversityIndex;
  final int independentOutletsCount;
}
