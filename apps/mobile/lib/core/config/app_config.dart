import 'package:flutter/foundation.dart';

@immutable
class AppConfig {
  const AppConfig({required this.apiBaseUri});

  factory AppConfig.fromEnvironment() {
    const raw = String.fromEnvironment(
      'KEFE_API_BASE_URL',
      defaultValue: 'http://localhost:8000',
    );
    return AppConfig(apiBaseUri: Uri.parse(raw));
  }

  final Uri apiBaseUri;
}
