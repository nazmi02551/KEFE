import 'package:flutter/foundation.dart';

enum CurationStateModel {
  draftSubmitted,
  communityPeerReview,
  editorialApproved,
  rejectedWithReason,
}

@immutable
class CommunityDilemmaProposalModel {
  const CommunityDilemmaProposalModel({
    required this.proposalId,
    required this.proposedTitle,
    required this.proposedContext,
    required this.curationState,
    required this.neutralityScore,
    required this.supporterCount,
  });

  final String proposalId;
  final String proposedTitle;
  final String proposedContext;
  final CurationStateModel curationState;
  final double neutralityScore;
  final int supporterCount;
}
