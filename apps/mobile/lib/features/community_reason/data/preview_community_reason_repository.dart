import 'community_reason_repository.dart';

class PreviewCommunityReasonRepository implements CommunityReasonRepository {
  final List<CommunityReasonItem> _items = [
    const CommunityReasonItem(
      id: 'preview-reason-1',
      tags: ['FAIRNESS'],
      text: 'Farklı ihtiyaçları aynı kuralla değerlendirmek her zaman adil olmayabilir.',
      reactionCounts: {'RESONATES': 12, 'USEFUL': 8},
    ),
    const CommunityReasonItem(
      id: 'preview-reason-2',
      tags: ['RULES'],
      text: 'Öngörülebilir ortak kurallar herkese aynı başlangıç noktası sağlar.',
      reactionCounts: {'RESONATES': 9, 'USEFUL': 11},
    ),
  ];

  @override
  Future<CommunityReasonSnapshot> fetch(String sessionId) async {
    final counts = <String, int>{};
    for (final item in _items) {
      for (final tag in item.tags) {
        counts[tag] = (counts[tag] ?? 0) + 1;
      }
    }
    return CommunityReasonSnapshot(
      items: List.unmodifiable(_items),
      tagPatternCounts: counts,
      sampleSize: _items.length,
      methodologyNote: 'Product Preview sample. Descriptive only; not Signal or truth ranking.',
    );
  }

  @override
  Future<CommunityReasonReceipt> publish({
    required String sessionId,
    required List<String> tags,
    String? text,
  }) async {
    final item = CommunityReasonItem(
      id: 'preview-reason-${_items.length + 1}',
      tags: List.unmodifiable(tags),
      text: text,
      reactionCounts: const {},
    );
    _items.insert(0, item);
    return CommunityReasonReceipt(
      id: item.id,
      tags: item.tags,
      text: text,
      moderationState: text == null ? 'NOT_REQUIRED' : 'PENDING',
    );
  }

  @override
  Future<void> react({required String reasonId, required String reaction}) async {}

  @override
  Future<void> report({required String reasonId, required String code}) async {}
}
