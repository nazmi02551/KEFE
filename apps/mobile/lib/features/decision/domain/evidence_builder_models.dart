import 'package:flutter/foundation.dart';

enum EvidenceCategoryModel {
  academicPeerReviewed,
  officialGovernmentStat,
  investigativeJournalism,
  institutionalReport,
}

enum EvidenceVerificationStatusModel {
  unverified,
  communityVerified,
  expertAudited,
}

@immutable
class StructuredEvidenceItemModel {
  const StructuredEvidenceItemModel({
    required this.evidenceId,
    required this.caseVersionId,
    required this.category,
    required this.title,
    required this.publisher,
    required this.verificationStatus,
    required this.createdAt,
    this.reasonId,
    this.sourceUrl,
    this.doiOrDocRef,
  });

  final String evidenceId;
  final String caseVersionId;
  final String? reasonId;
  final EvidenceCategoryModel category;
  final String title;
  final String publisher;
  final String? sourceUrl;
  final String? doiOrDocRef;
  final EvidenceVerificationStatusModel verificationStatus;
  final DateTime createdAt;
}
