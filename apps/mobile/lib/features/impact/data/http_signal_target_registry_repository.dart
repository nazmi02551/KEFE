import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../decision/data/http_decision_repository.dart';
import '../domain/signal_target_models.dart';
import 'signal_target_registry_repository.dart';

/// HTTP adapter for [SignalTargetRegistryRepository].
///
/// Calls GET /v1/signals/{signalId}/target-registry and deserializes the
/// [SignalTargetRegistryReportModel] response.
///
/// Invariants:
/// - Returns an empty report (no targets) when the registry is empty,
///   not an error — this is a valid state while dispatch targets are
///   being proposed and verified.
/// - Raises [ApiFailure] for non-200 responses.
/// - 404 signals are surfaced as [ApiFailure] with status 404.
class HttpSignalTargetRegistryRepository
    implements SignalTargetRegistryRepository {
  HttpSignalTargetRegistryRepository({
    required this.baseUrl,
    http.Client? client,
  }) : _client = client ?? http.Client();

  final String baseUrl;
  final http.Client _client;

  @override
  Future<SignalTargetRegistryReportModel> fetchTargetRegistry(
    String signalId,
  ) async {
    final uri = Uri.parse(
      '$baseUrl/v1/signals/${Uri.encodeComponent(signalId)}/target-registry',
    );
    final response = await _client.get(
      uri,
      headers: {'Accept': 'application/json'},
    );

    if (response.statusCode != 200) {
      throw ApiFailure(
        'FAILED_TO_FETCH_TARGET_REGISTRY',
        response.statusCode,
      );
    }

    final body =
        jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    return SignalTargetRegistryReportModel.fromJson(body);
  }
}