import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/data/http_decision_repository.dart';
import 'package:kefe_mobile/features/privacy/application/privacy_controller.dart';
import 'package:kefe_mobile/features/privacy/data/preview_privacy_repository.dart';
import 'package:kefe_mobile/features/privacy/data/privacy_repository.dart';
import 'package:kefe_mobile/features/privacy/presentation/privacy_screen.dart';

void main() {
  for (final locale in const [Locale('tr', 'TR'), Locale('en', 'US')]) {
    testWidgets(
      'validated deletion waits for explicit completion in ${locale.languageCode}',
      (tester) async {
        await _pumpPrivacy(
          tester,
          locale: locale,
          repository: _DeletionRepository(
            receipt: PrivacyDeletionReceipt(
              receiptId: 'sensitive-receipt-id',
              deletedAt: DateTime.utc(2026, 8, 31, 4, 30),
              policyVersion: 'sensitive-policy-version',
            ),
          ),
        );

        await _confirmDeletion(tester, locale);

        expect(
          find.byKey(const ValueKey('privacy-delete-complete')),
          findsOneWidget,
        );
        expect(find.byKey(const ValueKey('welcome-sentinel')), findsNothing);
        expect(
          find.text(
            locale.languageCode == 'tr'
                ? 'Verilerin silindi'
                : 'Your data has been deleted',
          ),
          findsOneWidget,
        );
        expect(
          find.textContaining(
            locale.languageCode == 'tr'
                ? 'Toplu katkılar anonimleştirildi.'
                : 'Aggregate contributions were anonymized.',
          ),
          findsOneWidget,
        );
        for (final sensitive in const [
          'sensitive-receipt-id',
          '2026-08-31',
          'sensitive-policy-version',
        ]) {
          expect(find.textContaining(sensitive), findsNothing);
        }

        await tester.tapAt(const Offset(1, 1));
        await tester.pumpAndSettle();
        expect(
          find.byKey(const ValueKey('privacy-delete-complete')),
          findsOneWidget,
        );
        expect(find.byKey(const ValueKey('welcome-sentinel')), findsNothing);

        await tester.binding.handlePopRoute();
        await tester.pumpAndSettle();
        expect(
          find.byKey(const ValueKey('privacy-delete-complete')),
          findsOneWidget,
        );

        await tester.tap(find.byKey(const ValueKey('privacy-delete-continue')));
        await tester.pumpAndSettle();
        expect(find.byKey(const ValueKey('welcome-sentinel')), findsOneWidget);
      },
    );
  }

  testWidgets('Product Preview reports sample reset without production claim', (
    tester,
  ) async {
    await _pumpPrivacy(
      tester,
      locale: const Locale('en', 'US'),
      repository: PreviewPrivacyRepository(),
    );

    await _confirmDeletion(tester, const Locale('en', 'US'));

    expect(find.text('Preview data reset'), findsOneWidget);
    expect(
      find.text(
        'Product Preview sample data was reset. No production account or live data was deleted.',
      ),
      findsOneWidget,
    );
    expect(find.text('Your data has been deleted'), findsNothing);
    expect(find.textContaining('preview-deletion-receipt'), findsNothing);
    expect(find.textContaining('PRODUCT_PREVIEW_ONLY'), findsNothing);
  });

  testWidgets('failed deletion never shows completion or navigates', (
    tester,
  ) async {
    await _pumpPrivacy(
      tester,
      locale: const Locale('en', 'US'),
      repository: const _FailingDeletionRepository(),
    );

    await _confirmDeletion(tester, const Locale('en', 'US'));

    expect(find.byKey(const ValueKey('privacy-delete-complete')), findsNothing);
    expect(find.byKey(const ValueKey('welcome-sentinel')), findsNothing);
    expect(find.byKey(const ValueKey('privacy-error-surface')), findsOneWidget);
  });

  test('executable contract guards completion and isolation boundaries', () {
    final contract =
        jsonDecode(
              File(
                '../../docs/contracts/privacy-deletion-completion-confirmation.v1.json',
              ).readAsStringSync(),
            )
            as Map<String, Object?>;
    final trigger = contract['trigger']! as Map<String, Object?>;
    final production =
        contract['production_presentation']! as Map<String, Object?>;
    final preview = contract['preview_presentation']! as Map<String, Object?>;
    final interaction = contract['interaction']! as Map<String, Object?>;
    final preserved = contract['preserved']! as Map<String, Object?>;
    final presentationSource = File(
      'lib/features/privacy/presentation/privacy_controls_section.dart',
    ).readAsStringSync();
    final previewSource = File(
      'lib/features/privacy/data/preview_privacy_repository.dart',
    ).readAsStringSync();

    expect(trigger['valid_repository_receipt_required'], isTrue);
    expect(trigger['failed_deletion_shows_completion'], isFalse);
    expect(production['receipt_id_visible'], isFalse);
    expect(production['deletion_timestamp_visible'], isFalse);
    expect(preview['typed_receipt_provenance_required'], isTrue);
    expect(preview['policy_string_inference_allowed'], isFalse);
    expect(interaction['barrier_dismissible'], isFalse);
    expect(interaction['system_back_dismissible'], isFalse);
    expect(interaction['successful_final_route'], '/welcome');
    expect(preserved['exact_delete_token'], 'DELETE');
    expect(preserved['api_changed'], isFalse);
    expect(presentationSource, contains('barrierDismissible: false'));
    expect(presentationSource, contains('canPop: false'));
    expect(presentationSource, contains("context.go('/welcome')"));
    expect(presentationSource, isNot(contains('PRODUCT_PREVIEW_ONLY')));
    expect(previewSource, contains('isProductPreview: true'));
  });
}

Future<void> _confirmDeletion(WidgetTester tester, Locale locale) async {
  await tester.tap(find.byKey(const ValueKey('privacy-delete')));
  await tester.pumpAndSettle();
  await tester.enterText(
    find.byKey(const ValueKey('privacy-delete-confirmation')),
    'DELETE',
  );
  await tester.tap(
    find.text(
      locale.languageCode == 'tr' ? 'Kalıcı olarak sil' : 'Delete permanently',
    ),
  );
  await tester.pumpAndSettle();
}

Future<void> _pumpPrivacy(
  WidgetTester tester, {
  required Locale locale,
  required PrivacyRepository repository,
}) async {
  final router = GoRouter(
    initialLocation: '/privacy',
    routes: [
      GoRoute(path: '/privacy', builder: (_, _) => const PrivacyScreen()),
      GoRoute(
        path: '/welcome',
        builder: (_, _) => const Scaffold(
          body: Center(
            child: Text('welcome', key: ValueKey('welcome-sentinel')),
          ),
        ),
      ),
    ],
  );
  addTearDown(router.dispose);

  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        privacyExperienceEnabledProvider.overrideWithValue(true),
        privacyRepositoryProvider.overrideWithValue(repository),
      ],
      child: MaterialApp.router(
        locale: locale,
        supportedLocales: KefeStrings.supportedLocales,
        localizationsDelegates: const [
          KefeStringsDelegate(),
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        theme: KefeTheme.light(),
        darkTheme: KefeTheme.dark(),
        routerConfig: router,
      ),
    ),
  );
  await tester.pumpAndSettle();
}

class _DeletionRepository implements PrivacyRepository {
  const _DeletionRepository({required this.receipt});

  final PrivacyDeletionReceipt receipt;

  @override
  Future<Map<String, Object?>> export() => throw UnimplementedError();

  @override
  Future<PrivacyDeletionReceipt> delete() async => receipt;
}

class _FailingDeletionRepository implements PrivacyRepository {
  const _FailingDeletionRepository();

  @override
  Future<Map<String, Object?>> export() => throw UnimplementedError();

  @override
  Future<PrivacyDeletionReceipt> delete() =>
      throw ApiFailure('PRIVACY_DELETE_RECEIPT_INVALID', 422);
}
