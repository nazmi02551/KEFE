import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../../core/config/app_config.dart';
import '../../decision/data/decision_repository.dart';
import '../../decision/data/http_decision_repository.dart';
import '../domain/progress_models.dart';
import 'progress_repository.dart';

class HttpProgressRepository implements ProgressRepository {
  HttpProgressRepository({
    required AppConfig config,
    required http.Client client,
    required CredentialStore credentialStore,
  }) : _config = config,
       _client = client,
       _credentialStore = credentialStore;

  final AppConfig _config;
  final http.Client _client;
  final CredentialStore _credentialStore;

  @override
  Future<ProgressEnvelope> fetchProgress() async {
    final token = await _credentialStore.read();
    if (token == null || token.isEmpty) {
      throw ApiFailure('AUTH_REQUIRED', 401);
    }

    final response = await _request(
      () => _client.get(
        _config.apiBaseUri.resolve('/v1/me/progress'),
        headers: {'authorization': 'Bearer $token'},
      ),
    );
    final body = _decode(response);
    final offer = (body['account_offer'] as Map).cast<String, Object?>();
    final progress = (body['progress'] as Map).cast<String, Object?>();
    final methodology = (body['methodology'] as Map).cast<String, Object?>();

    return ProgressEnvelope(
      accountOffer: AccountOffer(
        eligible: offer['eligible'] as bool,
        placement: offer['placement'] as String,
        blocking: offer['blocking'] as bool,
        dismissible: offer['dismissible'] as bool,
        continueAsGuestAvailable: offer['continue_as_guest_available'] as bool,
        accountCreationAvailable: offer['account_creation_available'] as bool,
      ),
      progress: MyKefeProgress(
        readiness: progress['readiness'] as String,
        meaningfulWeighCount: progress['meaningful_weigh_count'] as int,
        distinctCaseCount: progress['distinct_case_count'] as int,
        distinctDomainCount: progress['distinct_domain_count'] as int,
        firstCommittedAt: _date(progress['first_committed_at']),
        lastCommittedAt: _date(progress['last_committed_at']),
        recentCases: (progress['recent_cases'] as List<Object?>)
            .cast<Map>()
            .map((raw) {
              final item = raw.cast<String, Object?>();
              return RecentProgressCase(
                caseId: item['case_id'] as String,
                caseVersionId: item['case_version_id'] as String,
                title: item['title'] as String,
                primaryDomain: item['primary_domain'] as String,
                committedAt: DateTime.parse(item['committed_at'] as String),
              );
            })
            .toList(growable: false),
      ),
      journey: _journey(body['journey']),
      methodology: methodology.map(
        (key, value) => MapEntry(key, value.toString()),
      ),
    );
  }

  MyKefeJourney _journey(Object? raw) {
    if (raw is! Map) return const MyKefeJourney.empty();
    final map = raw.cast<String, Object?>();
    final domainRaw = map['domain_activity'];
    final recentRaw = map['recent_journeys'];

    final domainActivity = domainRaw is List
        ? domainRaw
              .whereType<Map>()
              .map((item) {
                final value = item.cast<String, Object?>();
                return MyKefeDomainActivity(
                  primaryDomain: value['primary_domain'] as String,
                  committedWeighCount: value['committed_weigh_count'] as int,
                  lastCommittedAt: _date(value['last_committed_at']),
                );
              })
              .toList(growable: false)
        : const <MyKefeDomainActivity>[];

    final recentJourneys = recentRaw is List
        ? recentRaw
              .whereType<Map>()
              .map((item) {
                final value = item.cast<String, Object?>();
                final initialCommittedAt = _date(value['initial_committed_at']);
                final latestDecisionAt = _date(value['latest_decision_at']);
                if (initialCommittedAt == null || latestDecisionAt == null) {
                  throw const FormatException(
                    'Journey timestamps are required',
                  );
                }
                return MyKefeRecentJourney(
                  caseId: value['case_id'] as String,
                  caseVersionId: value['case_version_id'] as String,
                  title: value['title'] as String,
                  primaryDomain: value['primary_domain'] as String,
                  initialCommittedAt: initialCommittedAt,
                  latestDecisionAt: latestDecisionAt,
                  decisionUpdateCount: value['decision_update_count'] as int,
                  reflectionCompleted: value['reflection_completed'] as bool,
                );
              })
              .toList(growable: false)
        : const <MyKefeRecentJourney>[];

    return MyKefeJourney(
      decisionUpdateCount: map['decision_update_count'] as int? ?? 0,
      revisitedCaseCount: map['revisited_case_count'] as int? ?? 0,
      reflectionCompletionCount:
          map['reflection_completion_count'] as int? ?? 0,
      domainActivity: domainActivity,
      recentJourneys: recentJourneys,
    );
  }

  DateTime? _date(Object? value) {
    if (value is! String || value.isEmpty) return null;
    return DateTime.parse(value);
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
