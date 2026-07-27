import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../decision/application/decision_controller.dart';
import '../data/context_repository.dart';
import '../domain/context_models.dart';

final contextSnapshotProvider = FutureProvider.autoDispose
    .family<CaseContextSnapshot, String>((ref, caseVersionId) async {
  final repository = ref.read(decisionRepositoryProvider);
  return repository.fetchContext(caseVersionId);
});
