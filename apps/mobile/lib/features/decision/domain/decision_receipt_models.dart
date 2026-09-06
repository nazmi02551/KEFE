import 'package:flutter/foundation.dart';

@immutable
class DecisionReceiptModel {
  const DecisionReceiptModel({
    required this.receiptId,
    required this.caseVersionId,
    required this.committedChoice,
    required this.integrityDigest,
    required this.timestampUtc,
  });

  final String receiptId;
  final String caseVersionId;
  final String committedChoice;
  final String integrityDigest;
  final String timestampUtc;
}
