import 'dart:io';

import 'package:flutter/foundation.dart';

@immutable
class AppConfig {
  const AppConfig({required this.apiBaseUri, required this.requestTimeout});

  factory AppConfig.fromEnvironment() {
    const raw = String.fromEnvironment(
      'KEFE_API_BASE_URL',
      defaultValue: 'http://localhost:8000',
    );
    const timeoutSeconds = int.fromEnvironment(
      'KEFE_HTTP_TIMEOUT_SECONDS',
      defaultValue: 12,
    );
    return AppConfig(
      apiBaseUri: Uri.parse(raw),
      requestTimeout: Duration(seconds: timeoutSeconds),
    );
  }

  factory AppConfig.connectedAlphaFromEnvironment() {
    const raw = String.fromEnvironment('KEFE_API_BASE_URL');
    const timeoutSeconds = int.fromEnvironment(
      'KEFE_HTTP_TIMEOUT_SECONDS',
      defaultValue: 12,
    );
    return AppConfig.connectedAlpha(
      rawApiBaseUrl: raw,
      timeoutSeconds: timeoutSeconds,
    );
  }

  factory AppConfig.connectedAlpha({
    required String rawApiBaseUrl,
    int timeoutSeconds = 12,
  }) {
    final normalized = rawApiBaseUrl.trim();
    final uri = Uri.tryParse(normalized);
    if (normalized.isEmpty || uri == null || !uri.hasAuthority) {
      throw ArgumentError.value(
        rawApiBaseUrl,
        'rawApiBaseUrl',
        'Connected Alpha requires an absolute API URL.',
      );
    }
    if (uri.scheme.toLowerCase() != 'https') {
      throw ArgumentError.value(
        rawApiBaseUrl,
        'rawApiBaseUrl',
        'Connected Alpha requires HTTPS.',
      );
    }
    if (uri.userInfo.isNotEmpty || uri.query.isNotEmpty || uri.fragment.isNotEmpty) {
      throw ArgumentError.value(
        rawApiBaseUrl,
        'rawApiBaseUrl',
        'Connected Alpha API URL cannot contain credentials, query, or fragment.',
      );
    }

    final host = uri.host.toLowerCase();
    final parsedIp = InternetAddress.tryParse(host);
    final forbiddenHost = host == 'localhost' ||
        host == '0.0.0.0' ||
        host == '10.0.2.2' ||
        host.endsWith('.invalid') ||
        parsedIp?.isLoopback == true;
    if (host.isEmpty || forbiddenHost) {
      throw ArgumentError.value(
        rawApiBaseUrl,
        'rawApiBaseUrl',
        'Connected Alpha requires a non-local, non-reserved API host.',
      );
    }

    if (timeoutSeconds < 3 || timeoutSeconds > 60) {
      throw ArgumentError.value(
        timeoutSeconds,
        'timeoutSeconds',
        'Connected Alpha HTTP timeout must be between 3 and 60 seconds.',
      );
    }

    return AppConfig(
      apiBaseUri: uri,
      requestTimeout: Duration(seconds: timeoutSeconds),
    );
  }

  final Uri apiBaseUri;
  final Duration requestTimeout;
}
