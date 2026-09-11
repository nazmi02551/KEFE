// Tests for ExploreController (CAP-033, ADR-0141)
//
// Covers:
// - Initial state is empty, not loading
// - load() transitions to loading then settles with items
// - ClientTransportFailure surfaces as errorCode
// - Unexpected errors surface as UNEXPECTED_CLIENT_ERROR
// - Turkish tolerant search filter matches and excludes correctly
// - is_real_event = false on preview fixture (ADR-0133 preview invariant)

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/decision_repository.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';
import 'package:kefe_mobile/features/explore/application/explore_controller.dart';
import 'package:kefe_mobile/features/explore/domain/explore_search.dart';

// ---------------------------------------------------------------------------
// Stub repository
// ---------------------------------------------------------------------------

class _StubRepository implements DecisionRepository {
  _StubRepository({
    this.cases = const [],
    this.shouldFail = false,
    this.failureCode = 'NETWORK_UNAVAILABLE',
  });

  final List<DecisionCaseSummary> cases;
  final bool shouldFail;
  final String failureCode;

  @override
  Future<List<DecisionCaseSummary>> fetchExploreCases({int limit = 20}) async {
    if (shouldFail) throw ClientTransportFailure(code: failureCode);
    return cases.take(limit).toList();
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

DecisionCaseSummary _summary({
  required String id,
  required String title,
  String summary = 'Özet',
  String domain = 'GOVERNANCE',
  bool isRealEvent = false,
}) =>
    DecisionCaseSummary(
      id: id,
      versionId: '$id-v1',
      title: title,
      summary: summary,
      format: 'DILEMMA',
      domain: domain,
      risk: 'LOW',
      isRealEvent: isRealEvent,
    );

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

void main() {
  group('ExploreController initial state', () {
    test('starts empty, not loading, no error', () {
      final container = ProviderContainer(
        overrides: [
          decisionRepositoryProvider.overrideWithValue(_StubRepository()),
        ],
      );
      addTearDown(container.dispose);

      final state = container.read(exploreControllerProvider);
      expect(state.loading, isFalse);
      expect(state.items, isEmpty);
      expect(state.errorCode, isNull);
    });
  });

  group('ExploreController.load()', () {
    test('returns items on success', () async {
      final items = [
        _summary(id: 'c1', title: 'Birinci mesele'),
        _summary(id: 'c2', title: 'İkinci mesele'),
      ];
      final container = ProviderContainer(
        overrides: [
          decisionRepositoryProvider.overrideWithValue(
            _StubRepository(cases: items),
          ),
        ],
      );
      addTearDown(container.dispose);

      await container.read(exploreControllerProvider.notifier).load();
      final state = container.read(exploreControllerProvider);

      expect(state.loading, isFalse);
      expect(state.errorCode, isNull);
      expect(state.items.length, 2);
      expect(state.items[0].id, 'c1');
    });

    test('surfaces ClientTransportFailure as errorCode', () async {
      final container = ProviderContainer(
        overrides: [
          decisionRepositoryProvider.overrideWithValue(
            _StubRepository(shouldFail: true, failureCode: 'TIMEOUT'),
          ),
        ],
      );
      addTearDown(container.dispose);

      await container.read(exploreControllerProvider.notifier).load();
      final state = container.read(exploreControllerProvider);

      expect(state.loading, isFalse);
      expect(state.items, isEmpty);
      expect(state.errorCode, 'TIMEOUT');
    });

    test('surfaces unexpected errors as UNEXPECTED_CLIENT_ERROR', () async {
      // The stub throws a plain Exception (not ClientTransportFailure)
      final container = ProviderContainer(
        overrides: [
          decisionRepositoryProvider.overrideWithValue(
            _UnexpectedErrorRepository(),
          ),
        ],
      );
      addTearDown(container.dispose);

      await container.read(exploreControllerProvider.notifier).load();
      final state = container.read(exploreControllerProvider);

      expect(state.errorCode, 'UNEXPECTED_CLIENT_ERROR');
    });
  });

  group('Turkish tolerant search (ADR-0141)', () {
    final corpus = [
      _summary(id: 'a', title: 'Şehir planlaması sorunu'),
      _summary(id: 'b', title: 'Çevre kirliliği'),
      _summary(id: 'c', title: 'Güvenlik açığı raporu'),
      _summary(id: 'd', title: 'İklim değişikliği'),
    ];

    bool match(String query, DecisionCaseSummary item) =>
        matchesExploreSearchQuery(
          query: query,
          fields: [item.title, item.summary, item.domain],
        );

    test('exact ascii query matches Turkish title', () {
      // 'sehir' should match 'Şehir'
      expect(match('sehir', corpus[0]), isTrue);
    });

    test('query with Turkish chars matches normalized title', () {
      // 'çevre' normalizes to 'cevre' and matches 'Çevre'
      expect(match('Çevre', corpus[1]), isTrue);
      expect(match('cevre', corpus[1]), isTrue);
    });

    test('unrelated query does not match', () {
      expect(match('okyanus', corpus[0]), isFalse);
    });

    test('empty query matches all', () {
      for (final item in corpus) {
        expect(match('', item), isTrue);
      }
    });

    test('multi-token query: all tokens must match', () {
      // 'guvenlik acigi' matches 'Güvenlik açığı raporu' (açığı→acigi)
      expect(match('guvenlik acigi', corpus[2]), isTrue);
      // 'guvenlik raporu' also matches
      expect(match('guvenlik raporu', corpus[2]), isTrue);
      // 'guvenlik okyanus' does not match (okyanus absent)
      expect(match('guvenlik okyanus', corpus[2]), isFalse);
    });

    test('Turkish I/İ/ı/i all normalize to i', () {
      // 'iklim' matches 'İklim'
      expect(match('iklim', corpus[3]), isTrue);
      expect(match('İklim', corpus[3]), isTrue);
    });
  });

  group('Preview is_real_event invariant (ADR-0133)', () {
    test('preview fixtures always return isRealEvent = false', () async {
      final items = [
        _summary(id: 'x', title: 'Gerçek bir olay değil', isRealEvent: false),
      ];
      final container = ProviderContainer(
        overrides: [
          decisionRepositoryProvider.overrideWithValue(
            _StubRepository(cases: items),
          ),
        ],
      );
      addTearDown(container.dispose);

      await container.read(exploreControllerProvider.notifier).load();
      final state = container.read(exploreControllerProvider);

      for (final item in state.items) {
        // Preview must not claim real-event status without server editorial review
        expect(item.isRealEvent, isFalse);
      }
    });
  });
}

// Helper: repository that throws an unexpected (non-domain) error
class _UnexpectedErrorRepository implements DecisionRepository {
  @override
  Future<List<DecisionCaseSummary>> fetchExploreCases({int limit = 20}) async {
    throw Exception('Unexpected internal failure');
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}