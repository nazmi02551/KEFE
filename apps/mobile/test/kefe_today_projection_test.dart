import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kefe_mobile/core/config/app_config.dart';
import 'package:kefe_mobile/features/decision/data/http_decision_repository.dart';

final config = AppConfig(
  apiBaseUri: Uri.parse('https://api.example.com'),
  requestTimeout: Duration(seconds: 5),
);

Map<String, Object?> summary({Object? isRealEvent}) {
  final result = <String, Object?>{
    'case_id': '11111111-1111-4111-8111-111111111111',
    'case_version_id': '22222222-2222-4222-8222-222222222222',
    'version_no': 1,
    'title': 'Governed real event',
    'summary': 'Source-reviewed Case.',
    'base_format': 'DILEMMA',
    'primary_domain': 'DAILY_LIFE',
    'content_risk': 'L0',
  };
  if (isRealEvent != null) result['is_real_event'] = isRealEvent;
  return result;
}

HttpDecisionRepository repositoryFor(Object? isRealEvent) {
  final client = MockClient((request) async {
    expect(request.url.path, '/v1/cases');
    return http.Response(
      jsonEncode({
        'items': [summary(isRealEvent: isRealEvent)],
      }),
      200,
      headers: const {'content-type': 'application/json'},
    );
  });
  return HttpDecisionRepository(
    config: config,
    client: client,
    credentialStore: MemoryCredentialStore(),
  );
}

void main() {
  test(
    'only exact JSON true marks an Explore summary as a real event',
    () async {
      expect(
        (await repositoryFor(true).fetchExploreCases()).single.isRealEvent,
        isTrue,
      );
      expect(
        (await repositoryFor('true').fetchExploreCases()).single.isRealEvent,
        isFalse,
      );
      expect(
        (await repositoryFor(null).fetchExploreCases()).single.isRealEvent,
        isFalse,
      );
    },
  );
}
