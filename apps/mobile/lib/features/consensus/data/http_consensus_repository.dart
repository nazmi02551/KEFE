import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../../core/config/app_config.dart';
import '../../decision/data/decision_repository.dart';
import '../../decision/data/http_decision_repository.dart';
import '../domain/consensus_models.dart';
import 'consensus_repository.dart';

class HttpConsensusRepository implements ConsensusRepository {
  HttpConsensusRepository({
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
  Future<List<ConsensusCard>> fetchCards({
    required String sessionId,
    required String caseVersionId,
  }) async {
    final headers = await _authorizedHeaders();
    final body = _decode(
      await _request(
        () => _client.get(
          _uri('/v1/weigh-sessions/$sessionId/consensus-cards'),
          headers: headers,
        ),
      ),
    );
    final items = (body['items'] as List<Object?>? ?? const [])
        .cast<Map<String, Object?>>()
        .map(_parseCard)
        .toList(growable: false);
    if (items.any((card) => card.caseVersionId != caseVersionId)) {
      throw const ClientTransportFailure(code: 'CONSENSUS_CONTRACT_INVALID');
    }
    return items;
  }

  @override
  Future<ConsensusCard> participate({
    required String sessionId,
    required String caseVersionId,
    required String cardVersionId,
    required String stanceCode,
    required List<String> reasonTagCodes,
    required String idempotencyKey,
  }) async {
    final headers = await _authorizedHeaders(json: true);
    final body = _decode(
      await _request(
        () => _client.post(
          _uri(
            '/v1/weigh-sessions/$sessionId/consensus-cards/'
            '$cardVersionId/participation',
          ),
          headers: {...headers, 'Idempotency-Key': idempotencyKey},
          body: jsonEncode({
            'stance_code': stanceCode,
            'reason_tag_codes': reasonTagCodes,
          }),
        ),
      ),
    );
    final card = _parseCard(body);
    if (card.caseVersionId != caseVersionId || card.versionId != cardVersionId) {
      throw const ClientTransportFailure(code: 'CONSENSUS_CONTRACT_INVALID');
    }
    return card;
  }

  ConsensusCard _parseCard(Map<String, Object?> item) {
    final participationJson = item['participation'] as Map<String, Object?>?;
    final aggregateJson = item['aggregate'] as Map<String, Object?>?;
    final contributionClass = item['contribution_class'] as String? ?? 'EXPOSED';
    if (contributionClass != 'EXPOSED') {
      throw const ClientTransportFailure(code: 'CONSENSUS_CONTRACT_INVALID');
    }
    return ConsensusCard(
      id: item['card_id'] as String,
      versionId: item['card_version_id'] as String,
      caseVersionId: item['case_version_id'] as String,
      proposition: item['proposition'] as String,
      stanceCodes: (item['stance_codes'] as List<Object?>).cast<String>(),
      reasonTagCodes: (item['reason_tag_codes'] as List<Object?>).cast<String>(),
      maxReasonTags: item['max_reason_tags'] as int,
      methodologyVersion: item['methodology_version'] as String,
      participationState: item['participation_state'] as String,
      contributionClass: contributionClass,
      participation: participationJson == null
          ? null
          : ConsensusParticipation(
              stanceCode: participationJson['stance_code'] as String,
              reasonTagCodes:
                  (participationJson['reason_tag_codes'] as List<Object?>)
                      .cast<String>(),
              contributionClass:
                  participationJson['contribution_class'] as String,
              participatedAt: DateTime.parse(
                participationJson['participated_at'] as String,
              ),
            ),
      aggregate: aggregateJson == null
          ? null
          : ConsensusAggregate(
              sampleSize: aggregateJson['sample_size'] as int,
              stanceDistribution: _doubleMap(
                aggregateJson['stance_distribution'] as Map<String, Object?>,
              ),
              reasonPatternDistribution: _doubleMap(
                aggregateJson['reason_pattern_distribution']
                    as Map<String, Object?>,
              ),
              contributionClass:
                  aggregateJson['contribution_class'] as String,
              methodologyVersion:
                  aggregateJson['methodology_version'] as String,
              generatedAt: DateTime.parse(
                aggregateJson['generated_at'] as String,
              ),
              provenanceNote: aggregateJson['provenance_note'] as String,
            ),
    );
  }

  Map<String, double> _doubleMap(Map<String, Object?> values) => values.map(
        (key, value) => MapEntry(key, (value as num).toDouble()),
      );

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
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return decoded;
    }
    throw ApiFailure(
      decoded['code'] as String? ?? 'UNKNOWN_API_ERROR',
      response.statusCode,
    );
  }
}
