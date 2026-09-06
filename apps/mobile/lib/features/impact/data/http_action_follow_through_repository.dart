import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../decision/data/http_decision_repository.dart';
import '../domain/action_follow_through_models.dart';
import 'action_follow_through_repository.dart';

class HttpActionFollowThroughRepository
    implements ActionFollowThroughRepository {
  HttpActionFollowThroughRepository({
    required this.baseUrl,
    http.Client? client,
  }) : _client = client ?? http.Client();

  final String baseUrl;
  final http.Client _client;

  @override
  Future<List<ActionFollowThroughItem>> fetchActions({
    String? caseVersionId,
  }) async {
    final query =
        caseVersionId != null ? '?case_version_id=$caseVersionId' : '';
    final uri = Uri.parse('$baseUrl/v1/impact/actions$query');
    final response = await _client.get(
      uri,
      headers: {'Accept': 'application/json'},
    );

    if (response.statusCode != 200) {
      throw ApiFailure('FAILED_TO_FETCH_ACTIONS', response.statusCode);
    }

    final body = jsonDecode(utf8.decode(response.bodyBytes)) as List<dynamic>;
    return body
        .map(
          (item) =>
              ActionFollowThroughItem.fromJson(item as Map<String, dynamic>),
        )
        .toList(growable: false);
  }

  @override
  Future<ActionFollowThroughItem> proposeAction({
    required String caseVersionId,
    required String title,
    required String description,
    DateTime? targetCompletionDate,
  }) async {
    final uri = Uri.parse('$baseUrl/v1/impact/actions');
    final response = await _client.post(
      uri,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: jsonEncode({
        'case_version_id': caseVersionId,
        'title': title,
        'description': description,
        if (targetCompletionDate != null)
          'target_completion_date': targetCompletionDate.toIso8601String(),
      }),
    );

    if (response.statusCode != 201) {
      throw ApiFailure('FAILED_TO_PROPOSE_ACTION', response.statusCode);
    }

    final body = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    return ActionFollowThroughItem.fromJson(body);
  }
}
