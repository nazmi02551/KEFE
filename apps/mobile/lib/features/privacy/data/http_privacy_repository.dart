import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../../core/config/app_config.dart';
import '../../decision/data/decision_repository.dart';
import '../../decision/data/http_decision_repository.dart';
import 'privacy_repository.dart';

class HttpPrivacyRepository implements PrivacyRepository {
  HttpPrivacyRepository({
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
  Future<Map<String, Object?>> export() async {
    final response = await _request(
      () async => _client.get(
        _uri('/v1/me/privacy-export'),
        headers: await _authorizedHeaders(),
      ),
    );
    return _decode(response);
  }

  @override
  Future<PrivacyDeletionReceipt> delete() async {
    final response = await _request(
      () async => _client.delete(
        _uri('/v1/me'),
        headers: {
          ...await _authorizedHeaders(),
          'X-KEFE-Delete-Confirm': 'DELETE',
        },
      ),
    );
    final body = _decode(response);
    await _credentialStore.clear();
    return PrivacyDeletionReceipt(
      receiptId: body['receipt_id'] as String,
      deletedAt: DateTime.parse(body['deleted_at'] as String),
      policyVersion: body['policy_version'] as String,
    );
  }

  Future<Map<String, String>> _authorizedHeaders() async {
    final token = await _credentialStore.read();
    if (token == null || token.isEmpty) {
      throw const ClientTransportFailure(code: 'AUTH_REQUIRED');
    }
    return {'authorization': 'Bearer $token'};
  }

  Future<http.Response> _request(Future<http.Response> Function() action) async {
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
