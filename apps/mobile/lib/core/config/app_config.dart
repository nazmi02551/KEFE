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

  final Uri apiBaseUri;
  final Duration requestTimeout;
}
