import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../../core/config/app_config.dart';
import '../../../core/network/session_renewal_client.dart';
import '../../context/data/context_repository.dart';
import '../../context/domain/context_models.dart';
import '../domain/decision_models.dart';
import '../domain/reflection_models.dart';
import 'decision_repository.dart';
import 'http_decision_repository.dart';

class HttpReflectionDecisionRepository
    implements
        DecisionRepository,
        FlowRuntimeRepository,
        DecisionLineageRepository,
        ReflectionRepository,
        PerspectiveRepository,
        ContextRepository {
  HttpReflectionDecisionRepository({
    required AppConfig config,
    required http.Client client,
    required CredentialStore credentialStore,
    SessionRenewalCoordinator? sessionRenewalCoordinator,
  }) : _config = config,
       _client = client,
       _delegate = HttpDecisionRepository(
         config: config,
         client: client,
         credentialStore: credentialStore,
         sessionRenewalCoordinator: sessionRenewalCoordinator,
       );

  final AppConfig _config;
  final http.Client _client;
  final HttpDecisionRepository _delegate;

  Uri _uri(String path) => _config.apiBaseUri.resolve(path);

  @override
  Future<GuestCredential> ensureGuestCredential() =>
      _delegate.ensureGuestCredential();

  @override
  Future<List<DecisionCaseSummary>> fetchExploreCases({int limit = 20}) =>
      _delegate.fetchExploreCases(limit: limit);

  @override
  Future<DecisionCase> fetchCase(String caseId) => _delegate.fetchCase(caseId);

  @override
  Future<CaseContextSnapshot> fetchContext(String caseVersionId) =>
      _delegate.fetchContext(caseVersionId);

  @override
  Future<String> startSession(String caseId) => _delegate.startSession(caseId);

  @override
  Future<FlowRuntimeSnapshot> fetchFlowRuntime(String sessionId) =>
      _delegate.fetchFlowRuntime(sessionId);

  @override
  Future<void> recordFlowStepExposure({
    required String sessionId,
    required String stepCode,
    required String idempotencyKey,
  }) => _delegate.recordFlowStepExposure(
    sessionId: sessionId,
    stepCode: stepCode,
    idempotencyKey: idempotencyKey,
  );

  @override
  Future<void> answerRevision({
    required String sessionId,
    required String stepCode,
    required String questionId,
    required Object value,
  }) => _delegate.answerRevision(
    sessionId: sessionId,
    stepCode: stepCode,
    questionId: questionId,
    value: value,
  );

  @override
  Future<void> saveRevisionReason({
    required String sessionId,
    required String stepCode,
    required List<String> tags,
    required String? text,
  }) => _delegate.saveRevisionReason(
    sessionId: sessionId,
    stepCode: stepCode,
    tags: tags,
    text: text,
  );

  @override
  Future<void> commitRevision({
    required String sessionId,
    required String stepCode,
    required String idempotencyKey,
  }) => _delegate.commitRevision(
    sessionId: sessionId,
    stepCode: stepCode,
    idempotencyKey: idempotencyKey,
  );

  @override
  Future<void> answer({
    required String sessionId,
    required String questionId,
    required Object value,
  }) => _delegate.answer(
    sessionId: sessionId,
    questionId: questionId,
    value: value,
  );

  @override
  Future<void> savePrivateReason({
    required String sessionId,
    required List<String> tags,
    required String? text,
  }) =>
      _delegate.savePrivateReason(sessionId: sessionId, tags: tags, text: text);

  @override
  Future<void> commit({
    required String sessionId,
    required String idempotencyKey,
  }) => _delegate.commit(sessionId: sessionId, idempotencyKey: idempotencyKey);

  @override
  Future<RevealResult> reveal(String sessionId) => _delegate.reveal(sessionId);

  @override
  Future<PerspectiveResult> fetchPerspectives(String sessionId) =>
      _delegate.fetchPerspectives(sessionId);

  @override
  Future<ReflectionReadModel> fetchReflection({
    required String sessionId,
    required String stepCode,
  }) async {
    final headers = await _authorizedHeaders();
    final response = await _request(
      () => _client.get(
        _uri('/v1/weigh-sessions/$sessionId/reflection-steps/$stepCode'),
        headers: headers,
      ),
    );
    return ReflectionReadModel.fromJson(_decode(response));
  }

  @override
  Future<void> completeReflection({
    required String sessionId,
    required String stepCode,
    required String idempotencyKey,
  }) async {
    final headers = await _authorizedHeaders();
    final response = await _request(
      () => _client.post(
        _uri(
          '/v1/weigh-sessions/$sessionId/reflection-steps/$stepCode/complete',
        ),
        headers: {...headers, 'Idempotency-Key': idempotencyKey},
      ),
    );
    _decode(response);
  }

  Future<Map<String, String>> _authorizedHeaders() async {
    final credential = await ensureGuestCredential();
    return {'authorization': 'Bearer ${credential.accessToken}'};
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
