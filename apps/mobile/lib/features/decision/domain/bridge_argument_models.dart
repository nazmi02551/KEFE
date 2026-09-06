import 'package:flutter/foundation.dart';

@immutable
class BridgeArgumentItemModel {
  const BridgeArgumentItemModel({
    required this.id,
    required this.caseVersionId,
    required this.synthesisThesis,
    required this.connectingValues,
    required this.crossGroupSupportRate,
    required this.sampleSize,
    required this.createdAt,
  });

  final String id;
  final String caseVersionId;
  final String synthesisThesis;
  final List<String> connectingValues;
  final double crossGroupSupportRate;
  final int sampleSize;
  final DateTime createdAt;
}
