import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../storage/credential_bundle.dart';
import '../storage/session_credential_store.dart';

class SessionContinuityFailure implements Exception {
  const SessionContinuityFailure(this.code, this.statusCode);

  final String code;
  final int statusCode;
}

class SessionRenewalCoordinator {
  SessionRenewalCoordinator({
    required AppConfig config,
    required http.Client client,
    required SessionCredentialStore credentialStore,
    this.proactiveSkew = const Duration(seconds: 60),
    DateTime Function()? now,
  }) : _config = config,
       _client = client,
       _credentialStore = credentialStore,
       _now = now ?? DateTime.now;

  final AppConfig _config;
  final http.Client _client;
  final SessionCredentialStore _credentialStore;
  final Duration proactiveSkew;
  final DateTime Function() _now;

  Future<SessionCredentialBundle>? _renewalInFlight;

  Uri _uri(String path) => _config.apiBaseUri.resolve(path);

  Future<SessionCredentialBundle?> ensureCurrent() async {
    final bundle = await _credentialStore.readBundle();
    if (bundle != null &&
        bundle.accessExpiresAt.isAfter(_now().toUtc().add(proactiveSkew))) {
      return bundle;
    }
    if (bundle != null) {
      return _singleFlight(() => _renew(bundle));
    }

    final legacyAccess = await _credentialStore.read();
    if (legacyAccess == null || legacyAccess.isEmpty) return null;
    return _singleFlight(() => _bootstrap(legacyAccess));
  }

  Future<SessionCredentialBundle?> renewAfterExpired(
    String rejectedAccessToken,
  ) async {
    final bundle = await _credentialStore.readBundle();
    if (bundle != null && bundle.accessToken != rejectedAccessToken) {
      return bundle;
    }
    if (bundle != null) {
      return _singleFlight(() => _renew(bundle));
    }

    final legacyAccess = await _credentialStore.read();
    if (legacyAccess == null || legacyAccess.isEmpty) return null;
    return _singleFlight(() => _bootstrap(legacyAccess));
  }

  Future<SessionCredentialBundle> _singleFlight(
    Future<SessionCredentialBundle> Function() action,
  ) async {
    final current = _renewalInFlight;
    if (current != null) return current;

    final future = action();
    _renewalInFlight = future;
    try {
      return await future;
    } finally {
      if (identical(_renewalInFlight, future)) {
        _renewalInFlight = null;
      }
    }
  }

  Future<SessionCredentialBundle> _renew(
    SessionCredentialBundle current,
  ) async {
    final response = await _client
        .post(
          _uri('/v1/identity/session/renew'),
          headers: const {'content-type': 'application/json'},
          body: jsonEncode({'renewal_token': current.renewalToken}),
        )
        .timeout(_config.requestTimeout);
    final body = _decode(response);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw SessionContinuityFailure(
        _failureCode(
          serverCode: body['code'] as String? ?? 'AUTH_RENEWAL_INVALID',
          actorKind: current.actorKind,
        ),
        response.statusCode,
      );
    }
    return _persistBundle(body);
  }

  Future<SessionCredentialBundle> _bootstrap(String legacyAccess) async {
    final response = await _client
        .post(
          _uri('/v1/identity/session/continuity/bootstrap'),
          headers: {'authorization': 'Bearer $legacyAccess'},
        )
        .timeout(_config.requestTimeout);
    final body = _decode(response);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw SessionContinuityFailure(
        _failureCode(
          serverCode: body['code'] as String? ?? 'AUTH_TOKEN_INVALID',
          legacy: true,
        ),
        response.statusCode,
      );
    }
    return _persistBundle(body);
  }

  Future<SessionCredentialBundle> _persistBundle(
    Map<String, Object?> body,
  ) async {
    try {
      final bundle = SessionCredentialBundle.fromApiJson(body);
      await _credentialStore.writeBundle(bundle);
      return bundle;
    } on FormatException {
      throw const SessionContinuityFailure(
        'SESSION_RENEWAL_RESPONSE_INVALID',
        502,
      );
    }
  }

  static Map<String, Object?> _decode(http.Response response) {
    if (response.body.isEmpty) return <String, Object?>{};
    try {
      final decoded = jsonDecode(response.body);
      return decoded is Map<String, Object?> ? decoded : <String, Object?>{};
    } on FormatException {
      return <String, Object?>{};
    }
  }

  static String _failureCode({
    required String serverCode,
    String? actorKind,
    bool legacy = false,
  }) {
    const terminalCodes = {
      'AUTH_RENEWAL_INVALID',
      'AUTH_RENEWAL_REPLAYED',
      'AUTH_SESSION_CONTINUITY_EXPIRED',
      'AUTH_TOKEN_EXPIRED',
      'AUTH_TOKEN_INVALID',
      'AUTH_TOKEN_REVOKED',
    };
    if (!terminalCodes.contains(serverCode)) return serverCode;
    if (legacy) return 'AUTH_LEGACY_CONTINUITY_REQUIRED';
    return actorKind == 'ACCOUNT'
        ? 'AUTH_ACCOUNT_REAUTHENTICATION_REQUIRED'
        : 'AUTH_GUEST_CONTINUITY_REQUIRED';
  }
}

class RenewingHttpClient extends http.BaseClient {
  RenewingHttpClient({
    required http.Client inner,
    required SessionRenewalCoordinator coordinator,
  }) : _inner = inner,
       _coordinator = coordinator;

  final http.Client _inner;
  final SessionRenewalCoordinator _coordinator;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final originalAuthorization = _authorization(request.headers);
    if (originalAuthorization == null) return _inner.send(request);

    SessionCredentialBundle? current;
    try {
      current = await _coordinator.ensureCurrent();
    } on SessionContinuityFailure catch (failure) {
      return _failureResponse(request, failure);
    }
    final firstToken =
        current?.accessToken ?? _bearerToken(originalAuthorization);
    final first = await _buffer(
      await _inner.send(_clone(request, accessToken: firstToken)),
    );
    if (first.statusCode != 401 || first.errorCode != 'AUTH_TOKEN_EXPIRED') {
      return first.asStreamed(request);
    }

    SessionCredentialBundle? renewed;
    try {
      renewed = await _coordinator.renewAfterExpired(firstToken);
    } on SessionContinuityFailure catch (failure) {
      return _failureResponse(request, failure);
    }
    if (renewed == null) return first.asStreamed(request);
    return _inner.send(_clone(request, accessToken: renewed.accessToken));
  }

  @override
  void close() => _inner.close();

  static String? _authorization(Map<String, String> headers) {
    for (final entry in headers.entries) {
      if (entry.key.toLowerCase() == 'authorization') return entry.value;
    }
    return null;
  }

  static String _bearerToken(String authorization) {
    final parts = authorization.split(' ');
    return parts.length == 2 ? parts[1] : authorization;
  }

  static http.Request _clone(
    http.BaseRequest source, {
    required String accessToken,
  }) {
    if (source is! http.Request) {
      throw http.ClientException(
        'Authorized session retry requires an HTTP request body snapshot',
        source.url,
      );
    }
    final clone = http.Request(source.method, source.url)
      ..followRedirects = source.followRedirects
      ..maxRedirects = source.maxRedirects
      ..persistentConnection = source.persistentConnection
      ..headers.addAll(source.headers)
      ..bodyBytes = source.bodyBytes;
    clone.headers['authorization'] = 'Bearer $accessToken';
    return clone;
  }

  static Future<_BufferedResponse> _buffer(
    http.StreamedResponse response,
  ) async {
    return _BufferedResponse(
      bodyBytes: await response.stream.toBytes(),
      statusCode: response.statusCode,
      headers: response.headers,
      isRedirect: response.isRedirect,
      persistentConnection: response.persistentConnection,
      reasonPhrase: response.reasonPhrase,
    );
  }

  static http.StreamedResponse _failureResponse(
    http.BaseRequest request,
    SessionContinuityFailure failure,
  ) {
    final bytes = utf8.encode(jsonEncode({'code': failure.code}));
    return http.StreamedResponse(
      http.ByteStream.fromBytes(bytes),
      failure.statusCode,
      contentLength: bytes.length,
      headers: const {'content-type': 'application/json'},
      request: request,
    );
  }
}

class _BufferedResponse {
  const _BufferedResponse({
    required this.bodyBytes,
    required this.statusCode,
    required this.headers,
    required this.isRedirect,
    required this.persistentConnection,
    required this.reasonPhrase,
  });

  final List<int> bodyBytes;
  final int statusCode;
  final Map<String, String> headers;
  final bool isRedirect;
  final bool persistentConnection;
  final String? reasonPhrase;

  String? get errorCode {
    try {
      final decoded = jsonDecode(utf8.decode(bodyBytes));
      return decoded is Map<String, Object?>
          ? decoded['code'] as String?
          : null;
    } on FormatException {
      return null;
    }
  }

  http.StreamedResponse asStreamed(http.BaseRequest request) {
    return http.StreamedResponse(
      http.ByteStream.fromBytes(bodyBytes),
      statusCode,
      contentLength: bodyBytes.length,
      headers: headers,
      isRedirect: isRedirect,
      persistentConnection: persistentConnection,
      reasonPhrase: reasonPhrase,
      request: request,
    );
  }
}
