import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/features/consensus/application/consensus_controller.dart';
import 'package:kefe_mobile/features/consensus/data/consensus_repository.dart';
import 'package:kefe_mobile/features/consensus/domain/consensus_models.dart';

void main() {
  test(
    'Consensus controller clears per-card draft and advances across cards',
    () async {
      final repository = _TwoCardConsensusRepository();
      final container = ProviderContainer(
        overrides: [
          consensusExperienceEnabledProvider.overrideWithValue(true),
          consensusRepositoryProvider.overrideWithValue(repository),
        ],
      );
      addTearDown(container.dispose);

      final controller = container.read(consensusControllerProvider.notifier);
      await controller.load(sessionId: 'session-1', caseVersionId: 'version-1');

      expect(
        container.read(consensusControllerProvider).uiState,
        ConsensusUiState.eligible,
      );
      expect(
        container.read(consensusControllerProvider).activeCard?.id,
        'card-1',
      );
      expect(
        container.read(consensusControllerProvider).activeCard?.versionId,
        'card-1-v1',
      );

      controller.selectStance('AGREE');
      controller.toggleReasonTag('FAIRNESS');
      await controller.submit();

      final afterFirst = container.read(consensusControllerProvider);
      expect(afterFirst.uiState, ConsensusUiState.eligible);
      expect(afterFirst.activeCard?.id, 'card-2');
      expect(afterFirst.activeCard?.versionId, 'card-2-v1');
      expect(afterFirst.selectedStance, isNull);
      expect(afterFirst.selectedReasonTags, isEmpty);

      controller.selectStance('MIXED');
      await controller.submit();

      final completed = container.read(consensusControllerProvider);
      expect(completed.uiState, ConsensusUiState.participated);
      expect(completed.cards.every((card) => card.participated), isTrue);
      expect(repository.idempotencyKeys.length, 2);
      expect(repository.idempotencyKeys.toSet().length, 2);
    },
  );
}

class _TwoCardConsensusRepository implements ConsensusRepository {
  final List<String> idempotencyKeys = [];
  final Map<String, ConsensusCard> _cards = {
    'card-1': _eligibleCard('card-1'),
    'card-2': _eligibleCard('card-2'),
  };

  @override
  Future<List<ConsensusCard>> fetchCards({
    required String sessionId,
    required String caseVersionId,
  }) async => _cards.values.toList(growable: false);

  @override
  Future<ConsensusCard> participate({
    required String sessionId,
    required String caseVersionId,
    required String cardId,
    required String cardVersionId,
    required String stanceCode,
    required List<String> reasonTagCodes,
    required String idempotencyKey,
  }) async {
    idempotencyKeys.add(idempotencyKey);
    final current = _cards[cardId]!;
    expect(current.versionId, cardVersionId);
    final participation = ConsensusParticipation(
      stanceCode: stanceCode,
      reasonTagCodes: List.unmodifiable(reasonTagCodes),
      contributionClass: 'EXPOSED',
      participatedAt: DateTime.utc(2026, 7, 30),
    );
    final updated = current.copyWith(
      participationState: 'PARTICIPATED',
      participation: participation,
      aggregate: ConsensusAggregate(
        sampleSize: 1,
        stanceDistribution: {
          'AGREE': stanceCode == 'AGREE' ? 1 : 0,
          'MIXED': stanceCode == 'MIXED' ? 1 : 0,
          'DISAGREE': stanceCode == 'DISAGREE' ? 1 : 0,
        },
        reasonPatternDistribution: {for (final tag in reasonTagCodes) tag: 1},
        contributionClass: 'EXPOSED',
        methodologyVersion: 'TEST_V1',
        generatedAt: DateTime.utc(2026, 7, 30),
        provenanceNote: 'test',
      ),
    );
    _cards[cardId] = updated;
    return updated;
  }
}

ConsensusCard _eligibleCard(String id) => ConsensusCard(
  id: id,
  versionId: '$id-v1',
  caseVersionId: 'version-1',
  proposition: 'Proposition $id',
  stanceCodes: const ['AGREE', 'MIXED', 'DISAGREE'],
  reasonTagCodes: const ['FAIRNESS'],
  maxReasonTags: 1,
  methodologyVersion: 'TEST_V1',
  participationState: 'ELIGIBLE',
  contributionClass: 'EXPOSED',
);
