import 'share_repository.dart';

class PreviewShareRepository implements ShareRepository {
  final Map<String, PublicShare> _shares = {};

  @override
  Future<CreatedShare> create({
    required String sessionId,
    required bool includeDecision,
  }) async {
    if (includeDecision) {
      throw StateError('SHARE_DECISION_EXPOSURE_NOT_SUPPORTED');
    }
    final now = DateTime.now().toUtc();
    final token = 'preview-${now.microsecondsSinceEpoch}';
    final id = 'preview-share-${now.microsecondsSinceEpoch}';
    _shares[token] = PublicShare(
      id: id,
      caseId: '11111111-1111-4111-8111-111111111111',
      caseVersionId: '22222222-2222-4222-8222-222222222222',
      title: 'Product Preview Case',
      summary:
          'CASE-ONLY preview share; no sender decision or private reason is included.',
      primaryDomain: 'DAILY_LIFE',
      createdAt: now,
      expiresAt: now.add(const Duration(days: 7)),
    );
    return CreatedShare(
      id: id,
      token: token,
      expiresAt: now.add(const Duration(days: 7)),
      includeDecision: false,
    );
  }

  @override
  Future<PublicShare> read(String token) async {
    final existing = _shares[token];
    if (existing != null) return existing;
    final now = DateTime.now().toUtc();
    return PublicShare(
      id: 'preview-share-inbound',
      caseId: '11111111-1111-4111-8111-111111111111',
      caseVersionId: '22222222-2222-4222-8222-222222222222',
      title: 'Product Preview Case',
      summary: 'Shared Case preview. The receiver still weighs before Reveal.',
      primaryDomain: 'DAILY_LIFE',
      createdAt: now,
      expiresAt: now.add(const Duration(days: 7)),
    );
  }

  @override
  Future<void> revoke(String shareId) async {
    _shares.removeWhere((_, value) => value.id == shareId);
  }
}
