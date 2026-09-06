import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../domain/action_follow_through_models.dart';
import 'preview_action_follow_through_repository.dart';

abstract class ActionFollowThroughRepository {
  Future<List<ActionFollowThroughItem>> fetchActions({String? caseVersionId});
  Future<ActionFollowThroughItem> proposeAction({
    required String caseVersionId,
    required String title,
    required String description,
    DateTime? targetCompletionDate,
  });
}

final actionFollowThroughRepositoryProvider =
    Provider<ActionFollowThroughRepository>((ref) {
      return PreviewActionFollowThroughRepository();
    });
