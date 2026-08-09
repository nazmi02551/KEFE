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
    final actorId = await _resolveActorId();
    final response = await _request(
      () async => _client.delete(
        _uri('/v1/me'),
        headers: {
          ...await _authorizedHeaders(),
          'X-KEFE-Delete-Confirm': 'DELETE:$actorId',
        },
      ),
    );
    final body = _decode(response);
    if (body['actor_id'] != actorId ||
        body['private_data_deleted'] != true ||
        body['aggregate_contributions_anonymized'] != true) {
      throw ApiFailure('PRIVACY_DELETE_RECEIPT_INVALID', 502);
    }
    final receipt = PrivacyDeletionReceipt(
      receiptId: body['receipt_id'] as String,
      deletedAt: DateTime.parse(body['deleted_at'] as String),
      policyVersion: body['policy_version'] as String,
    );
    await _credentialStore.clear();
    return receipt;
  }

  Future<String> _resolveActorId() async {
    final stored = (await _credentialStore.readActorId())?.trim();
    if (stored != null && stored.isNotEmpty) return stored;

    final data = await export();
    final rawActorId = data['actor_id'];
    if (rawActorId is! String || rawActorId.trim().isEmpty) {
      throw ApiFailure('PRIVACY_ACTOR_ID_UNAVAILABLE', 502);
    }
    final actorId = rawActorId.trim();
    await _credentialStore.writeActorId(actorId);
    return actorId;
  }

  Future<Map<String, String>> _authorizedHeaders() async {
    final token = await _credentialStore.read();
    if (token == null || token.isEmpty) {
      throw const ClientTransportFailure(code: 'AUTH_REQUIRED');
    }
    return {'authorization': 'Bearer $token'};
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
