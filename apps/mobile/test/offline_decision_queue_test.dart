import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/features/decision/data/offline_decision_queue.dart';

void main() {
  group('Offline-First Secure Draft Queue (CAP-078)', () {
    test('ADR-0158 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0158-offline-first-secure-draft-queue.md');
      final contract = File('../../docs/contracts/offline-draft-queue.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-OFFLINE-DRAFT-QUEUE-001'));
      expect(contract.readAsStringSync(), contains('zero_draft_loss'));
    });

    test('OfflineDecisionQueue enqueues, dedupes, and updates status', () {
      final queue = OfflineDecisionQueue();

      final item1 = QueuedDecisionSubmission(
        queueId: 'q-1',
        sessionId: 's-1',
        caseVersionId: 'cv-1',
        idempotencyKey: 'idem-key-1',
        responses: {'q-1': 'opt-a'},
        reasonText: 'Çevrimdışı kaydedilen gerekçe.',
        status: OfflineQueueItemStatus.pending,
        queuedAt: DateTime.now().toUtc(),
      );

      queue.enqueue(item1);
      expect(queue.pendingCount, 1);

      // Deduplication: trying to enqueue again with same idempotencyKey
      queue.enqueue(item1);
      expect(queue.items.length, 1);

      // Status transition
      queue.markSyncing('q-1');
      expect(queue.items.first.status, OfflineQueueItemStatus.syncing);

      queue.markCompleted('q-1');
      expect(queue.items.first.status, OfflineQueueItemStatus.completed);

      queue.clearCompleted();
      expect(queue.items.isEmpty, isTrue);
    });

    test('OfflineDecisionQueue increments retry count on failure', () {
      final queue = OfflineDecisionQueue();

      final item = QueuedDecisionSubmission(
        queueId: 'q-2',
        sessionId: 's-2',
        caseVersionId: 'cv-2',
        idempotencyKey: 'idem-key-2',
        responses: {},
        status: OfflineQueueItemStatus.pending,
        queuedAt: DateTime.now().toUtc(),
      );

      queue.enqueue(item);
      queue.markFailed('q-2');

      expect(queue.items.first.status, OfflineQueueItemStatus.failed);
      expect(queue.items.first.retryCount, 1);
    });
  });
}
