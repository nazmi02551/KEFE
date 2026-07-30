abstract interface class ShareRepository {
  Future<CreatedShare> create({
    required String sessionId,
    required bool includeDecision,
  });

  Future<PublicShare> read(String token);

  Future<void> revoke(String shareId);
}

class CreatedShare {
  const CreatedShare({
    required this.id,
    required this.token,
    required this.expiresAt,
    required this.includeDecision,
  });

  final String id;
  final String token;
  final DateTime expiresAt;
  final bool includeDecision;

  String get deepLink => 'kefe://share/$token';
}

class PublicShare {
  const PublicShare({
    required this.id,
    required this.caseId,
    required this.caseVersionId,
    required this.title,
    required this.summary,
    required this.primaryDomain,
    required this.createdAt,
    required this.expiresAt,
    this.decision,
  });

  final String id;
  final String caseId;
  final String caseVersionId;
  final String title;
  final String summary;
  final String primaryDomain;
  final Map<String, Object?>? decision;
  final DateTime createdAt;
  final DateTime expiresAt;
}
