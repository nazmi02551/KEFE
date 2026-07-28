import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../../core/config/app_config.dart';
import '../../context/data/context_repository.dart';
import '../../context/domain/context_models.dart';
import '../domain/decision_models.dart';
import 'decision_repository.dart';

abstract interface class CredentialStore {
  Future<String?> read();
  Future<void> write(String token);
  Future<void> clear();
}

class MemoryCredentialStore implements CredentialStore {
  String? _token;

  @override
  Future<void> clear() async => _token = null;

  @override
  Future<String?> read() async => _token;

  @override
  Future<void> write(String token) async => _token = token;
}

class ApiFailure implements Exception {
  ApiFailure(this.code, this.statusCode);

  final String code;
  final int statusCode;

  @override
  String toString() => 'ApiFailure($statusCode, $code)';
}

class HttpDecisionRepository
    implements
        DecisionRepository,
        FlowRuntimeRepository,
        DecisionLineageRepository,
        PerspectiveRepository,
        ContextRepository {
  HttpDecisionRepository({
    required AppConfig config,
    required http.Client client,
    required CredentialStore credentialStore,
  }) : _config = config,
       _client = client,
       _credentialStore = credentialStore;

  final AppConfig _config;
  final http.Client _client;
  final CredentialStore _credentialStore;

  String? _token;

  Uri _uri(String path) => _config.apiBaseUri.resolve(path);

  @override
  Future<GuestCredential> ensureGuestCredential() async {
    final existing = _token ?? await _credentialStore.read();
    if (existing != null) {
      _token = existing;
      return GuestCredential(
        actorId: '',
        accessToken: existing,
        expiresAt: DateTime.now().toUtc().add(const Duration(days: 30)),
      );
    }
    final response = await _request(
      () => _client.post(
        _uri('/v1/identity/guest'),
        headers: const {'content-type': 'application/json'},
        body: jsonEncode({'platform': 'ANDROID'}),
      ),
    );
    final body = _decode(response);
    final credential = GuestCredential(
      actorId: body['actor_id'] as String,
      accessToken: body['access_token'] as String,
      expiresAt: DateTime.parse(body['expires_at'] as String),
    );
    _token = credential.accessToken;
    await _credentialStore.write(credential.accessToken);
    return credential;
  }

  @override
  Future<List<DecisionCaseSummary>> fetchExploreCases({int limit = 20}) async {
    final body = _decode(
      await _request(() => _client.get(_uri('/v1/cases?limit=$limit'))),
    );
    return (body['items'] as List<Object?>)
        .cast<Map<String, Object?>>()
        .map(
          (item) => DecisionCaseSummary(
            id: item['case_id'] as String,
            versionId: item['case_version_id'] as String,
            title: item['title'] as String,
            summary: item['summary'] as String,
            format: item['base_format'] as String,
            domain: item['primary_domain'] as String,
            risk: item['content_risk'] as String,
          ),
        )
        .toList(growable: false);
  }

  @override
  Future<DecisionCase> fetchCase(String caseId) async {
    final body = _decode(
      await _request(() => _client.get(_uri('/v1/cases/$caseId'))),
    );
    return DecisionCase(
      id: body['case_id'] as String,
      versionId: body['case_version_id'] as String,
      title: body['title'] as String,
      summary: body['summary'] as String,
      format: body['base_format'] as String,
      domain: body['primary_domain'] as String,
      risk: body['content_risk'] as String,
      questions: (body['questions'] as List<Object?>)
          .cast<Map<String, Object?>>()
          .map((item) {
            final schema =
                (item['response_schema'] as Map<String, Object?>?) ?? const {};
            return DecisionQuestion(
              id: item['question_id'] as String,
              prompt: item['prompt'] as String,
              responseType: item['response_type'] as String,
              required: item['required'] as bool? ?? true,
              options: (item['options'] as List<Object?>? ?? const [])
                  .cast<String>(),
              responseSchema: schema,
            );
          })
          .toList(growable: false),
    );
  }

  @override
  Future<CaseContextSnapshot> fetchContext(String caseVersionId) async {
    final body = _decode(
      await _request(
        () => _client.get(
          _uri('/v1/case-versions/$caseVersionId/context'),
        ),
      ),
    );
    return CaseContextSnapshot(
      caseVersionId: body['case_version_id'] as String,
      blocks: (body['blocks'] as List<Object?>)
          .cast<Map<String, Object?>>()
          .map(
            (item) => CaseContextBlock(
              id: item['context_block_id'] as String,
              displayOrder: item['display_order'] as int,
              disclosureLevel: item['disclosure_level'] as String,
              title: item['title'] as String,
              body: item['body'] as String,
              claimStatus: item['claim_status'] as String,
              sourceIds: (item['source_ids'] as List<Object?>).cast<String>(),
            ),
          )
          .toList(growable: false),
      sources: (body['sources'] as List<Object?>)
          .cast<Map<String, Object?>>()
          .map(
            (item) => CaseContextSource(
              id: item['source_id'] as String,
              title: item['title'] as String,
              publisher: item['publisher'] as String,
              sourceKind: item['source_kind'] as String,
              url: item['url'] == null
                  ? null
                  : Uri.parse(item['url'] as String),
              publishedAt: item['published_at'] == null
                  ? null
                  : DateTime.parse(item['published_at'] as String),
            ),
          )
          .toList(growable: false),
    );
  }

  @override
  Future<String> startSession(String caseId) async {
    final headers = await _authorizedHeaders();
    final response = await _request(
      () => _client.post(
        _uri('/v1/cases/$caseId/weigh-sessions'),
        headers: headers,
      ),
    );
    return _decode(response)['session_id'] as String;
  }

  @override
  Future<FlowRuntimeSnapshot> fetchFlowRuntime(String sessionId) async {
    final headers = await _authorizedHeaders();
    final body = _decode(
      await _request(
        () => _client.get(
          _uri('/v1/weigh-sessions/$sessionId/flow'),
          headers: headers,
        ),
      ),
    );
    return FlowRuntimeSnapshot.fromJson(body);
  }

  @override
  Future<void> recordFlowStepExposure({
    required String sessionId,
    required String stepCode,
    required String idempotencyKey,
  }) async {
    final headers = await _authorizedHeaders();
    final response = await _request(
      () => _client.post(
        _uri('/v1/weigh-sessions/$sessionId/flow-steps/$stepCode/exposures'),
        headers: {...headers, 'Idempotency-Key': idempotencyKey},
      ),
    );
    _decode(response);
  }

  @override
  Future<void> answerRevision({
    required String sessionId,
    required String stepCode,
    required String questionId,
    required Object value,
  }) async {
    final headers = await _authorizedHeaders(json: true);
    final response = await _request(
      () => _client.put(
        _uri('/v1/weigh-sessions/$sessionId/decision-steps/$stepCode/responses'),
        headers: headers,
        body: jsonEncode({
          'responses': [
            {'question_id': questionId, 'value': value},
          ],
        }),
      ),
    );
    _decode(response);
  }

  @override
  Future<void> saveRevisionReason({
    required String sessionId,
    required String stepCode,
    required List<String> tags,
    required String? text,
  }) async {
    final headers = await _authorizedHeaders(json: true);
    final response = await _request(
      () => _client.put(
        _uri('/v1/weigh-sessions/$sessionId/decision-steps/$stepCode/reason'),
        headers: headers,
        body: jsonEncode({'tags': tags, 'text': text}),
      ),
    );
    _decode(response);
  }

  @override
  Future<void> commitRevision({
    required String sessionId,
    required String stepCode,
    required String idempotencyKey,
  }) async {
    final headers = await _authorizedHeaders();
    final response = await _request(
      () => _client.post(
        _uri('/v1/weigh-sessions/$sessionId/decision-steps/$stepCode/commit'),
        headers: {...headers, 'Idempotency-Key': idempotencyKey},
      ),
    );
    _decode(response);
  }

  @override
  Future<void> answer({
    required String sessionId,
    required String questionId,
    required Object value,
  }) async {
    final headers = await _authorizedHeaders(json: true);
    final response = await _request(
      () => _client.put(
        _uri('/v1/weigh-sessions/$sessionId/responses'),
        headers: headers,
        body: jsonEncode({
          'responses': [
            {'question_id': questionId, 'value': value},
          ],
        }),
      ),
    );
    _decode(response);
  }

  @override
  Future<void> savePrivateReason({
    required String sessionId,
    required List<String> tags,
    required String? text,
  }) async {
    final headers = await _authorizedHeaders(json: true);
    final response = await _request(
      () => _client.put(
        _uri('/v1/weigh-sessions/$sessionId/reason'),
        headers: headers,
        body: jsonEncode({'tags': tags, 'text': text}),
      ),
    );
    _decode(response);
  }

  @override
  Future<void> commit({
    required String sessionId,
    required String idempotencyKey,
  }) async {
    final headers = await _authorizedHeaders();
    final response = await _request(
      () => _client.post(
        _uri('/v1/weigh-sessions/$sessionId/commit'),
        headers: {...headers, 'Idempotency-Key': idempotencyKey},
      ),
    );
    _decode(response);
  }

  @override
  Future<RevealResult> reveal(String sessionId) async {
    final headers = await _authorizedHeaders();
    final body = _decode(
      await _request(
        () => _client.get(
          _uri('/v1/weigh-sessions/$sessionId/reveal'),
          headers: headers,
        ),
      ),
    );
    return RevealResult(
      layer: body['layer'] as String,
      sampleSize: body['n'] as int,
      confidence: body['confidence'] as String,
      values: (body['result'] as Map<String, Object?>).map(
        (key, value) => MapEntry(key, (value as num).toDouble()),
      ),
    );
  }

  @override
  Future<PerspectiveResult> fetchPerspectives(String sessionId) async {
    final headers = await _authorizedHeaders();
    final body = _decode(
      await _request(
        () => _client.get(
          _uri('/v1/weigh-sessions/$sessionId/perspectives'),
          headers: headers,
        ),
      ),
    );
    final methodology = body['methodology'] as Map<String, Object?>;
    final cards = (body['cards'] as List<Object?>)
        .cast<Map<String, Object?>>()
        .map(_parsePerspectiveCard)
        .whereType<PerspectiveCard>()
        .take(4)
        .toList(growable: false);
    return PerspectiveResult(
      sessionId: body['session_id'] as String,
      caseVersionId: body['case_version_id'] as String,
      cards: cards,
      methodology: PerspectiveMethodology(
        mode: methodology['mode'] as String,
        sampleKind: methodology['sample_kind'] as String,
        sampleSize: methodology['sample_size'] as int,
        generatedAt: DateTime.parse(methodology['generated_at'] as String),
        provenanceNote: methodology['provenance_note'] as String,
      ),
    );
  }

  PerspectiveCard? _parsePerspectiveCard(Map<String, Object?> item) {
    final slot = switch (item['slot']) {
      'NEAR' => PerspectiveSlot.near,
      'OPPOSING' => PerspectiveSlot.opposing,
      'BRIDGE' => PerspectiveSlot.bridge,
      'ALTERNATIVE_CONTEXT' => PerspectiveSlot.alternativeContext,
      _ => null,
    };
    if (slot == null) return null;
    return PerspectiveCard(
      id: item['perspective_id'] as String,
      slot: slot,
      body: item['body'] as String,
      sourceKind: item['source_kind'] as String,
      provenanceLabel: item['provenance_label'] as String,
      moderationState: item['moderation_state'] as String,
    );
  }

  Future<Map<String, String>> _authorizedHeaders({bool json = false}) async {
    final credential = await ensureGuestCredential();
    return {
      'authorization': 'Bearer ${credential.accessToken}',
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
