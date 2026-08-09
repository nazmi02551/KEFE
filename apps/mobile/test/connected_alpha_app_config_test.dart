import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/config/app_config.dart';

void main() {
  group('Connected Alpha AppConfig', () {
    test('accepts an external HTTPS endpoint and bounded timeout', () {
      final config = AppConfig.connectedAlpha(
        rawApiBaseUrl: 'https://alpha-api.example.com/v1',
        timeoutSeconds: 15,
      );

      expect(config.apiBaseUri, Uri.parse('https://alpha-api.example.com/v1'));
      expect(config.requestTimeout, const Duration(seconds: 15));
    });

    test('rejects empty or non-HTTPS endpoint', () {
      expect(
        () => AppConfig.connectedAlpha(rawApiBaseUrl: ''),
        throwsArgumentError,
      );
      expect(
        () => AppConfig.connectedAlpha(
          rawApiBaseUrl: 'http://alpha-api.example.com',
        ),
        throwsArgumentError,
      );
    });

    test('rejects local emulator and reserved hosts', () {
      for (final url in <String>[
        'https://localhost:8000',
        'https://127.0.0.1:8000',
        'https://[::1]:8000',
        'https://0.0.0.0:8000',
        'https://10.0.2.2:8000',
        'https://beta-api.invalid',
      ]) {
        expect(
          () => AppConfig.connectedAlpha(rawApiBaseUrl: url),
          throwsArgumentError,
          reason: url,
        );
      }
    });

    test('rejects credentials query and fragment in API URL', () {
      for (final url in <String>[
        'https://user:secret@alpha-api.example.com',
        'https://alpha-api.example.com?token=secret',
        'https://alpha-api.example.com#fragment',
      ]) {
        expect(
          () => AppConfig.connectedAlpha(rawApiBaseUrl: url),
          throwsArgumentError,
          reason: url,
        );
      }
    });

    test('rejects timeouts outside the reviewed range', () {
      expect(
        () => AppConfig.connectedAlpha(
          rawApiBaseUrl: 'https://alpha-api.example.com',
          timeoutSeconds: 2,
        ),
        throwsArgumentError,
      );
      expect(
        () => AppConfig.connectedAlpha(
          rawApiBaseUrl: 'https://alpha-api.example.com',
          timeoutSeconds: 61,
        ),
        throwsArgumentError,
      );
    });
  });
}
