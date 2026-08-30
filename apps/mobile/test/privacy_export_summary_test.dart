import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/privacy/application/privacy_controller.dart';
import 'package:kefe_mobile/features/privacy/application/privacy_export_summary.dart';
import 'package:kefe_mobile/features/privacy/data/privacy_repository.dart';
import 'package:kefe_mobile/features/privacy/presentation/privacy_screen.dart';

const actorId = '11111111-1111-4111-8111-111111111111';

Map<String, Object?> validExport({int totalRecords = 2}) => {
  'schema_version': 'privacy-export.v2',
  'actor_id': actorId,
  'actor_kind': 'GUEST',
  'generated_at': '2026-08-30T12:00:00Z',
  'manifest': <String, Object?>{
    'dataset_counts': <String, Object?>{
      'private_reasons': totalRecords == 0 ? 0 : 1,
      'share_records': 0,
      'weigh_sessions': totalRecords == 0 ? 0 : totalRecords - 1,
    },
    'total_records': totalRecords,
    'empty_datasets': totalRecords == 0
        ? <Object?>['private_reasons', 'share_records', 'weigh_sessions']
        : <Object?>['share_records'],
  },
  'product_data': <String, Object?>{
    'private_reasons': <Object?>[
      <String, Object?>{'text': 'private content'},
    ],
  },
  'data_sha256': 'secret-digest-not-for-presentation',
};

void main() {
  group('PrivacyExportSummary', () {
    test('accepts a consistent v2 manifest without reading product data', () {
      final summary = PrivacyExportSummary.tryParse(validExport());

      expect(summary, isNotNull);
      expect(summary!.totalRecords, 2);
      expect(summary.nonEmptyDatasetCount, 2);
    });

    test('rejects a legacy export without a v2 manifest', () {
      final summary = PrivacyExportSummary.tryParse({
        'product_data': <String, Object?>{
          'weigh_sessions': <Object?>[1, 2, 3],
        },
      });

      expect(summary, isNull);
    });

    test('rejects inconsistent totals instead of recounting product data', () {
      final export = validExport();
      final manifest = export['manifest']! as Map<String, Object?>;
      manifest['total_records'] = 99;

      expect(PrivacyExportSummary.tryParse(export), isNull);
    });

    test('rejects an inaccurate empty-dataset list', () {
      final export = validExport();
      final manifest = export['manifest']! as Map<String, Object?>;
      manifest['empty_datasets'] = <Object?>[];

      expect(PrivacyExportSummary.tryParse(export), isNull);
    });
  });

  for (final locale in const [Locale('tr', 'TR'), Locale('en', 'US')]) {
    testWidgets(
      'shows aggregate export summary without sensitive fields in ${locale.languageCode}',
      (tester) async {
        String? clipboardText;
        TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
            .setMockMethodCallHandler(SystemChannels.platform, (call) async {
              if (call.method == 'Clipboard.setData') {
                clipboardText =
                    (call.arguments as Map<Object?, Object?>)['text']
                        as String?;
              }
              return null;
            });
        addTearDown(
          () => TestDefaultBinaryMessengerBinding
              .instance
              .defaultBinaryMessenger
              .setMockMethodCallHandler(SystemChannels.platform, null),
        );
        await _pumpPrivacy(tester, locale: locale, export: validExport());

        await tester.tap(find.byKey(const ValueKey('privacy-export')));
        await tester.pumpAndSettle();

        expect(
          find.byKey(const ValueKey('privacy-export-summary')),
          findsOneWidget,
        );
        expect(
          find.byKey(const ValueKey('privacy-export-record-count')),
          findsOneWidget,
        );
        expect(
          find.byKey(const ValueKey('privacy-export-group-count')),
          findsOneWidget,
        );
        expect(
          find.text(
            locale.languageCode == 'tr'
                ? '2 kayıt dahil'
                : '2 records included',
          ),
          findsOneWidget,
        );
        expect(
          find.text(
            locale.languageCode == 'tr'
                ? '2 veri grubunda kayıt var'
                : '2 data groups contain records',
          ),
          findsOneWidget,
        );
        expect(find.textContaining(actorId), findsNothing);
        expect(find.textContaining('private content'), findsNothing);
        expect(
          find.textContaining('secret-digest-not-for-presentation'),
          findsNothing,
        );
        expect(clipboardText, isNotNull);
        final clipboardJson =
            jsonDecode(clipboardText!) as Map<String, Object?>;
        expect(clipboardJson['actor_id'], actorId);
        expect(clipboardJson['product_data'], isNotNull);
      },
    );
  }

  testWidgets('malformed manifest keeps the generic copied confirmation', (
    tester,
  ) async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          SystemChannels.platform,
          (call) async => null,
        );
    addTearDown(
      () => TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(SystemChannels.platform, null),
    );
    final export = validExport();
    final manifest = export['manifest']! as Map<String, Object?>;
    manifest['total_records'] = 99;
    await _pumpPrivacy(
      tester,
      locale: const Locale('en', 'US'),
      export: export,
    );

    await tester.tap(find.byKey(const ValueKey('privacy-export')));
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('privacy-export-summary')), findsNothing);
    expect(find.text('Your data copy is ready'), findsOneWidget);
    expect(find.textContaining('copied to the clipboard'), findsOneWidget);
  });

  test('repository contract keeps the presentation and isolation boundary', () {
    final contract =
        jsonDecode(
              File(
                '../../docs/contracts/privacy-safe-mobile-export-summary.v1.json',
              ).readAsStringSync(),
            )
            as Map<String, Object?>;
    final presentation = contract['presentation']! as Map<String, Object?>;
    final isolation = contract['isolation']! as Map<String, Object?>;
    final source = File(
      'lib/features/privacy/presentation/privacy_controls_section.dart',
    ).readAsStringSync();

    expect(presentation['raw_dataset_keys_visible'], isFalse);
    expect(presentation['complete_json_clipboard_copy_preserved'], isTrue);
    expect(isolation['product_preview_repository_changed'], isFalse);
    for (final key in const [
      'privacy-export-summary',
      'privacy-export-record-count',
      'privacy-export-group-count',
    ]) {
      expect(source, contains("'$key'"));
    }
    expect(
      File(
        'lib/features/privacy/data/preview_privacy_repository.dart',
      ).readAsStringSync(),
      isNot(contains('privacy-export.v2')),
    );
  });
}

Future<void> _pumpPrivacy(
  WidgetTester tester, {
  required Locale locale,
  required Map<String, Object?> export,
}) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        privacyExperienceEnabledProvider.overrideWithValue(true),
        privacyRepositoryProvider.overrideWithValue(
          _ExportPrivacyRepository(export),
        ),
      ],
      child: MaterialApp(
        locale: locale,
        supportedLocales: KefeStrings.supportedLocales,
        localizationsDelegates: const [
          KefeStringsDelegate(),
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        home: const PrivacyScreen(),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

class _ExportPrivacyRepository implements PrivacyRepository {
  const _ExportPrivacyRepository(this.data);

  final Map<String, Object?> data;

  @override
  Future<Map<String, Object?>> export() async => data;

  @override
  Future<PrivacyDeletionReceipt> delete() => throw UnimplementedError();
}
