import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../../core/config/app_config.dart';
import '../../decision/data/decision_repository.dart';
import '../../decision/data/http_decision_repository.dart';
import 'community_reason_repository.dart';

class HttpCommunityReasonRepository implements CommunityReasonRepository {
  HttpCommunityReasonRepository({
    required AppConfig config,
    required http.Client client,
    required CredentialStore credentialStore,
  }) : _config = config,
       _client = client,
       _credentialStore = credentialStore;

  final AppConfig _config;
  final http.Client _client;
  final CredentialStore _credentialStore;

  Uri _uri(String path) => _config.apiBaseUri.resolve(path);

  @override
  Future<CommunityReasonReceipt> publish({
    required String sessionId,
    required List<String> tags,
    String? text,
  }) async {
    final body = _decode(
      await _request(
        () async => _client.post(
          _uri('/v1/weigh-sessions/$sessionId/community-reason'),
          headers: await _authorizedHeaders(json: true),
          body: jsonEncode({'tags': tags, 'text': text}),
        ),
      ),
    );
    return CommunityReasonReceipt(
      id: body['reason_id'] as String,
      tags: (body['tags'] as List<Object?>).cast<String>(),
      text: body['text'] as String?,
      moderationState: body['moderation_state'] as String,
    );
  }

  @override
  Future<CommunityReasonSnapshot> fetch(String caseVersionId) async {
    final body = _decode(
      await _request(
        () => _client.get(
          _uri('/v1/case-versions/$caseVersionId/community-reasons'),
        ),
      ),
    );
    final items = (body['items'] as List<Object?>? ?? const [])
        .cast<Map<String, Object?>>()
        .map(
          (item) => CommunityReasonItem(
            id: item['reason_id'] as String,
            tags: (item['tags'] as List<Object?>).cast<String>(),
            text: item['text'] as String?,
            reactionCounts: (item['reaction_counts'] as Map<String, Object?>)
                .map((key, value) => MapEntry(key, value as int)),
          ),
        )
        .toList(growable: false);
    return CommunityReasonSnapshot(
      items: items,
      tagPatternCounts: (body['tag_pattern_counts'] as Map<String, Object?>)
          .map((key, value) => MapEntry(key, value as int)),
      sampleSize: body['sample_size'] as int,
      methodologyNote: body['methodology_note'] as String,
    );
  }

  @override
  Future<void> react({
    required String reasonId,
    required String reaction,
  }) async {
    final response = await _request(
      () async => _client.put(
        _uri('/v1/community-reasons/$reasonId/reaction'),
        headers: await _authorizedHeaders(json: true),
        body: jsonEncode({'reaction': reaction}),
      ),
    );
    _decode(response);
  }

  @override
  Future<void> report({required String reasonId, required String code}) async {
    final response = await _request(
      () async => _client.post(
        _uri('/v1/community-reasons/$reasonId/reports'),
        headers: await _authorizedHeaders(json: true),
        body: jsonEncode({'code': code}),
      ),
    );
    _decode(response);
  }

  Future<Map<String, String>> _authorizedHeaders({bool json = false}) async {
    final token = await _credentialStore.read();
    if (token == null || token.isEmpty) {
      throw const ClientTransportFailure(code: 'AUTH_REQUIRED');
    }
    return {
      'authorization': 'Bearer $token',
      if (json) 'content-type': 'application/json',
    };
  }

  Future<http.Response> _request(
    Future<http.Response> Function() action,
  ) async {
    try {
      return await action().timeout(_config.requestTimeout);
    } on TimeoutException {
      throw const ClientTransportFailure(code: 'NETWORK_TIMEOUT');
    } on http.ClientException {
      throw const ClientTransportFailure();
    }
  }

  Map<String, Object?> _decode(http.Response response) {
    final decoded = response.body.isEmpty
        ? <String, Object?>{}
        : (jsonDecode(response.body) as Map<String, Object?>);
    if (response.statusCode >= 200 && response.statusCode < 300) return decoded;
    throw ApiFailure(
      decoded['code'] as String? ?? 'UNKNOWN_API_ERROR',
      response.statusCode,
    );
  }
}
