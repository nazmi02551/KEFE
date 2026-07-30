import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../../core/config/app_config.dart';
import '../../decision/data/decision_repository.dart';
import '../../decision/data/http_decision_repository.dart';
import 'share_repository.dart';

class HttpShareRepository implements ShareRepository {
  HttpShareRepository({
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
  Future<CreatedShare> create({
    required String sessionId,
    required bool includeDecision,
  }) async {
    final headers = await _authorizedHeaders(json: true);
    final body = _decode(
      await _request(
        () => _client.post(
          _uri('/v1/shares'),
          headers: headers,
          body: jsonEncode({
            'session_id': sessionId,
            'include_decision': includeDecision,
          }),
        ),
      ),
    );
    return CreatedShare(
      id: body['share_id'] as String,
      token: body['token'] as String,
      expiresAt: DateTime.parse(body['expires_at'] as String),
      includeDecision: body['include_decision'] as bool,
    );
  }

  @override
  Future<PublicShare> read(String token) async {
    final body = _decode(
      await _request(
        () => _client.get(_uri('/v1/shares/${Uri.encodeComponent(token)}')),
      ),
    );
    return PublicShare(
      id: body['share_id'] as String,
      caseId: body['case_id'] as String,
      caseVersionId: body['case_version_id'] as String,
      title: body['title'] as String,
      summary: body['summary'] as String,
      primaryDomain: body['primary_domain'] as String,
      createdAt: DateTime.parse(body['created_at'] as String),
      expiresAt: DateTime.parse(body['expires_at'] as String),
    );
  }

  @override
  Future<void> revoke(String shareId) async {
    final headers = await _authorizedHeaders();
    await _request(
      () => _client.delete(_uri('/v1/shares/$shareId'), headers: headers),
      acceptNoContent: true,
    );
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
    Future<http.Response> Function() action, {
    bool acceptNoContent = false,
  }) async {
    try {
      final response = await action().timeout(_config.requestTimeout);
      if (acceptNoContent && response.statusCode == 204) return response;
      return response;
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
