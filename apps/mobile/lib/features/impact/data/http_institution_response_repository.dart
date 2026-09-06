import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../decision/data/http_decision_repository.dart';
import '../domain/institution_response_models.dart';
import 'institution_response_repository.dart';

class HttpInstitutionResponseRepository
    implements InstitutionResponseRepository {
  HttpInstitutionResponseRepository({
    required this.baseUrl,
    http.Client? client,
  }) : _client = client ?? http.Client();

  final String baseUrl;
  final http.Client _client;

  @override
  Future<List<InstitutionResponseItem>> fetchInstitutionResponses({
    String? caseVersionId,
  }) async {
    final query =
        caseVersionId != null ? '?case_version_id=$caseVersionId' : '';
    final uri = Uri.parse('$baseUrl/v1/impact/institution-responses$query');
    final response = await _client.get(
      uri,
      headers: {'Accept': 'application/json'},
    );

    if (response.statusCode != 200) {
      throw ApiFailure(
        'FAILED_TO_FETCH_INSTITUTION_RESPONSES',
        response.statusCode,
      );
    }

    final body = jsonDecode(utf8.decode(response.bodyBytes)) as List<dynamic>;
    return body
        .map(
          (item) =>
              InstitutionResponseItem.fromJson(item as Map<String, dynamic>),
        )
        .toList(growable: false);
  }
}
