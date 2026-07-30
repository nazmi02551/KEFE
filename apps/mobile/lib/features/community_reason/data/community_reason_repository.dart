abstract interface class CommunityReasonRepository {
  Future<CommunityReasonReceipt> publish({
    required String sessionId,
    required List<String> tags,
    String? text,
  });

  Future<CommunityReasonSnapshot> fetch(String caseVersionId);

  Future<void> react({required String reasonId, required String reaction});

  Future<void> report({required String reasonId, required String code});
}

class CommunityReasonReceipt {
  const CommunityReasonReceipt({
    required this.id,
    required this.tags,
    required this.moderationState,
    this.text,
  });

  final String id;
  final List<String> tags;
  final String? text;
  final String moderationState;
}

class CommunityReasonItem {
  const CommunityReasonItem({
    required this.id,
    required this.tags,
    required this.reactionCounts,
    this.text,
  });

  final String id;
  final List<String> tags;
  final String? text;
  final Map<String, int> reactionCounts;
}

class CommunityReasonSnapshot {
  const CommunityReasonSnapshot({
    required this.items,
    required this.tagPatternCounts,
    required this.sampleSize,
    required this.methodologyNote,
  });

  final List<CommunityReasonItem> items;
  final Map<String, int> tagPatternCounts;
  final int sampleSize;
  final String methodologyNote;
}
