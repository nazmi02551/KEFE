import '../domain/consensus_models.dart';
import 'consensus_repository.dart';

class PreviewConsensusRepository implements ConsensusRepository {
  final Map<String, ConsensusParticipation> _participations = {};

  static const _stanceCodes = ['AGREE', 'MIXED', 'DISAGREE'];
  static const _reasonCodes = [
    'FAIRNESS',
    'NEED',
    'RULES',
    'PRACTICAL_IMPACT',
  ];

  @override
  Future<List<ConsensusCard>> fetchCards({
    required String sessionId,
    required String caseVersionId,
  }) async {
    final card = _card(sessionId: sessionId, caseVersionId: caseVersionId);
    return [card];
  }

  @override
  Future<ConsensusCard> participate({
    required String sessionId,
    required String caseVersionId,
    required String cardVersionId,
    required String stanceCode,
    required List<String> reasonTagCodes,
    required String idempotencyKey,
  }) async {
    final expectedVersion = _versionId(caseVersionId);
    if (cardVersionId != expectedVersion || !_stanceCodes.contains(stanceCode)) {
      throw StateError('Invalid Product Preview Consensus participation');
    }
    if (reasonTagCodes.length > 2 ||
        reasonTagCodes.any((tag) => !_reasonCodes.contains(tag))) {
      throw StateError('Invalid Product Preview Consensus reason tags');
    }
    final key = '$sessionId::$cardVersionId';
    final existing = _participations[key];
    if (existing != null) {
      return _card(sessionId: sessionId, caseVersionId: caseVersionId);
    }
    _participations[key] = ConsensusParticipation(
      stanceCode: stanceCode,
      reasonTagCodes: List.unmodifiable(reasonTagCodes),
      contributionClass: 'EXPOSED',
      participatedAt: DateTime.utc(2026, 7, 30, 1, 30),
    );
    return _card(sessionId: sessionId, caseVersionId: caseVersionId);
  }

  ConsensusCard _card({
    required String sessionId,
    required String caseVersionId,
  }) {
    final versionId = _versionId(caseVersionId);
    final participation = _participations['$sessionId::$versionId'];
    return ConsensusCard(
      id: versionId,
      versionId: versionId,
      caseVersionId: caseVersionId,
      proposition:
          'Bu vakada adil bir karar, yalnız sonuca değil sürecin açık ve '
          'tutarlı olmasına da dayanmalıdır.',
      stanceCodes: _stanceCodes,
      reasonTagCodes: _reasonCodes,
      maxReasonTags: 2,
      methodologyVersion: 'CONSENSUS_WE_V1_PREVIEW',
      participationState: participation == null ? 'ELIGIBLE' : 'PARTICIPATED',
      contributionClass: 'EXPOSED',
      participation: participation,
      aggregate: participation == null ? null : _aggregate(participation),
    );
  }

  ConsensusAggregate _aggregate(ConsensusParticipation participation) {
    final stanceCounts = <String, int>{
      'AGREE': 214,
      'MIXED': 126,
      'DISAGREE': 72,
    };
    stanceCounts[participation.stanceCode] =
        (stanceCounts[participation.stanceCode] ?? 0) + 1;
    final reasonCounts = <String, int>{
      'FAIRNESS': 192,
      'NEED': 151,
      'RULES': 117,
      'PRACTICAL_IMPACT': 83,
    };
    for (final tag in participation.reasonTagCodes) {
      reasonCounts[tag] = (reasonCounts[tag] ?? 0) + 1;
    }
    final sampleSize = stanceCounts.values.fold<int>(0, (sum, value) => sum + value);
    return ConsensusAggregate(
      sampleSize: sampleSize,
      stanceDistribution: {
        for (final code in _stanceCodes) code: stanceCounts[code]! / sampleSize,
      },
      reasonPatternDistribution: {
        for (final code in _reasonCodes) code: reasonCounts[code]! / sampleSize,
      },
      contributionClass: 'EXPOSED',
      methodologyVersion: 'CONSENSUS_WE_V1_PREVIEW',
      generatedAt: DateTime.utc(2026, 7, 30, 1, 30),
      provenanceNote:
          'Deterministik Product Preview örneklemi. Bu EXPOSED dağılım ana '
          'pre-result sonuca dahil değildir ve Signal değildir.',
    );
  }

  String _versionId(String caseVersionId) => 'preview-consensus-$caseVersionId-v1';
}
