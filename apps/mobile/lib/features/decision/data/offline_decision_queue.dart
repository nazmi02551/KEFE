import 'package:flutter/foundation.dart';

enum OfflineQueueItemStatus {
  pending,
  syncing,
  completed,
  failed,
}

@immutable
class QueuedDecisionSubmission {
  const QueuedDecisionSubmission({
    required this.queueId,
    required this.sessionId,
    required this.caseVersionId,
    required this.idempotencyKey,
    required this.responses,
    required this.status,
    required this.queuedAt,
    this.reasonText,
    this.retryCount = 0,
  });

  final String queueId;
  final String sessionId;
  final String caseVersionId;
  final String idempotencyKey;
  final Map<String, dynamic> responses;
  final String? reasonText;
  final OfflineQueueItemStatus status;
  final DateTime queuedAt;
  final int retryCount;

  QueuedDecisionSubmission copyWith({
    OfflineQueueItemStatus? status,
    int? retryCount,
  }) {
    return QueuedDecisionSubmission(
      queueId: queueId,
      sessionId: sessionId,
      caseVersionId: caseVersionId,
      idempotencyKey: idempotencyKey,
      responses: responses,
      reasonText: reasonText,
      status: status ?? this.status,
      queuedAt: queuedAt,
      retryCount: retryCount ?? this.retryCount,
    );
  }
}

class OfflineDecisionQueue {
  final List<QueuedDecisionSubmission> _queue = [];

  List<QueuedDecisionSubmission> get items => List.unmodifiable(_queue);

  int get pendingCount =>
      _queue.where((e) => e.status == OfflineQueueItemStatus.pending).length;

  void enqueue(QueuedDecisionSubmission item) {
    // Avoid duplicate enqueue with same idempotencyKey
    final exists = _queue.any((e) => e.idempotencyKey == item.idempotencyKey);
    if (!exists) {
      _queue.add(item);
    }
  }

  void markSyncing(String queueId) {
    _updateStatus(queueId, OfflineQueueItemStatus.syncing);
  }

  void markCompleted(String queueId) {
    _updateStatus(queueId, OfflineQueueItemStatus.completed);
  }

  void markFailed(String queueId) {
    final idx = _queue.indexWhere((e) => e.queueId == queueId);
    if (idx != -1) {
      final current = _queue[idx];
      _queue[idx] = current.copyWith(
        status: OfflineQueueItemStatus.failed,
        retryCount: current.retryCount + 1,
      );
    }
  }

  void clearCompleted() {
    _queue.removeWhere((e) => e.status == OfflineQueueItemStatus.completed);
  }

  void _updateStatus(String queueId, OfflineQueueItemStatus status) {
    final idx = _queue.indexWhere((e) => e.queueId == queueId);
    if (idx != -1) {
      _queue[idx] = _queue[idx].copyWith(status: status);
    }
  }
}
