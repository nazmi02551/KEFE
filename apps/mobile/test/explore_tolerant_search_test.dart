import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/features/explore/domain/explore_search.dart';

void main() {
  test('contract keeps search local, ordered and non-personalized', () {
    final file = File('../../docs/contracts/explore-tolerant-search.v1.json');
    expect(file.existsSync(), isTrue);
    final contract =
        jsonDecode(file.readAsStringSync()) as Map<String, Object?>;
    final scope = contract['scope']! as Map<String, Object?>;
    final matching = contract['matching']! as Map<String, Object?>;

    expect(scope['execution'], 'ON_DEVICE_EPHEMERAL');
    expect(scope['preserve_catalog_order'], isTrue);
    expect(scope['remote_search'], isFalse);
    expect(matching['token_operator'], 'AND');
    expect(matching['ranking'], isFalse);
    expect(matching['recommendation'], isFalse);
    expect(matching['personalization'], isFalse);
  });

  test('normalization maps bounded Turkish characters and whitespace', () {
    expect(
      normalizeExploreSearchText('  İŞ   ÇÖZÜMÜ ŞÜPHE  '),
      'is cozumu suphe',
    );
    expect(normalizeExploreSearchText('EĞİTİM'), 'egitim');
    expect(normalizeExploreSearchText('I ı İ i'), 'i i i i');
  });

  test('all query tokens may match across governed searchable fields', () {
    expect(
      matchesExploreSearchQuery(
        query: 'kamusal yasam seffaflik',
        fields: const [
          'Kamu sözleşmeleri herkese açık olmalı mı?',
          'Şeffaflık ve kamu yararı arasındaki sınır.',
          'Kamusal yaşam',
        ],
      ),
      isTrue,
    );
    expect(
      matchesExploreSearchQuery(
        query: 'kamusal spor',
        fields: const ['Kamusal yaşam', 'Şeffaflık'],
      ),
      isFalse,
    );
    expect(
      matchesExploreSearchQuery(query: '   ', fields: const ['Her vaka']),
      isTrue,
    );
  });

  test('Explore presentation exposes localized live result status', () {
    final source = File(
      'lib/features/explore/presentation/discovery_explore_screen.dart',
    ).readAsStringSync();
    final strings = File(
      'lib/features/saved_cases/localization/saved_case_string_catalog.dart',
    ).readAsStringSync();

    expect(source, contains("ValueKey('explore-result-status')"));
    expect(source, contains('liveRegion: true'));
    expect(source, contains('strings.domainLabel(item.domain)'));
    expect(strings, contains('{count} vaka bulundu'));
    expect(strings, contains('{count} Cases found'));
  });
}
