import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../../core/config/app_config.dart';
import '../../decision/data/decision_repository.dart';
import '../../decision/data/http_decision_repository.dart';
import 'account_repository.dart';

class HttpAccountRepository implements AccountRepository {
  HttpAccountRepository({
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
  Future<OtpChallenge> requestOtp({
    required String channel,
    required String identifier,
  }) async {
    final body = _decode(
      await _request(
        () => _client.post(
          _uri('/v1/auth/otp/request'),
          headers: const {'content-type': 'application/json'},
          body: jsonEncode({'channel': channel, 'identifier': identifier}),
        ),
      ),
    );
    return OtpChallenge(
      id: body['challenge_id'] as String,
      destinationHint: body['destination_hint'] as String,
      expiresAt: DateTime.parse(body['expires_at'] as String),
    );
  }

  @override
  Future<OtpVerification> verifyOtp({
    required String challengeId,
    required String code,
  }) async {
    final body = _decode(
      await _request(
        () => _client.post(
          _uri('/v1/auth/otp/verify'),
          headers: const {'content-type': 'application/json'},
          body: jsonEncode({'challenge_id': challengeId, 'code': code}),
        ),
      ),
    );
    return OtpVerification(
      token: body['verification_token'] as String,
      expiresAt: DateTime.parse(body['expires_at'] as String),
    );
  }

  @override
  Future<AccountConversion> mergeGuest({
    required String verificationToken,
  }) async {
    final guestToken = await _credentialStore.read();
    if (guestToken == null || guestToken.isEmpty) {
      throw const ClientTransportFailure(code: 'AUTH_REQUIRED');
    }
    final body = _decode(
      await _request(
        () => _client.post(
          _uri('/v1/auth/guest-merge'),
          headers: {
            'authorization': 'Bearer $guestToken',
            'content-type': 'application/json',
          },
          body: jsonEncode({'verification_token': verificationToken}),
        ),
      ),
    );
    final accountToken = body['access_token'] as String;
    await _credentialStore.write(accountToken);
    return AccountConversion(
      actorId: body['actor_id'] as String,
      mergedExistingHistory: body['merged_from_actor_id'] != null,
    );
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
