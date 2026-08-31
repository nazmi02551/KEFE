import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/account/application/account_controller.dart';
import 'package:kefe_mobile/features/account/data/account_repository.dart';
import 'package:kefe_mobile/features/account/data/preview_account_repository.dart';
import 'package:kefe_mobile/features/account/presentation/account_conversion_screen.dart';
import 'package:kefe_mobile/features/decision/data/decision_repository.dart';
import 'package:kefe_mobile/features/decision/data/http_decision_repository.dart';

void main() {
  test(
    'invalid OTP preserves the challenge and can complete after correction',
    () async {
      final repository = _RecoveryAccountRepository(
        verifyErrorCode: 'AUTH_OTP_INVALID',
      );
      final container = _container(repository);
      addTearDown(container.dispose);
      final controller = container.read(accountControllerProvider.notifier);

      controller.setIdentifier('person@example.test');
      await controller.requestOtp();
      final challenge = container.read(accountControllerProvider).challenge;

      await controller.verifyAndMerge('123456');
      var state = container.read(accountControllerProvider);
      expect(state.uiState, AccountUiState.enterCode);
      expect(state.challenge, same(challenge));
      expect(state.errorCode, 'AUTH_OTP_INVALID');

      controller.retry();
      state = container.read(accountControllerProvider);
      expect(state.uiState, AccountUiState.enterCode);
      expect(state.challenge, same(challenge));
      expect(state.errorCode, isNull);

      repository.verifyErrorCode = null;
      await controller.verifyAndMerge('654321');
      state = container.read(accountControllerProvider);
      expect(state.uiState, AccountUiState.complete);
      expect(state.actorId, 'account-actor');
      expect(repository.verifyCalls, 2);
    },
  );

  for (final code in const [
    'AUTH_OTP_EXPIRED',
    'AUTH_OTP_CHALLENGE_USED',
    'AUTH_OTP_CHALLENGE_NOT_FOUND',
    'AUTH_OTP_ATTEMPTS_EXCEEDED',
  ]) {
    test('$code clears the challenge and preserves the destination', () async {
      final repository = _RecoveryAccountRepository(verifyErrorCode: code);
      final container = _container(repository);
      addTearDown(container.dispose);
      final controller = container.read(accountControllerProvider.notifier);

      controller.setIdentifier('person@example.test');
      await controller.requestOtp();
      await controller.verifyAndMerge('123456');

      var state = container.read(accountControllerProvider);
      expect(state.uiState, AccountUiState.error);
      expect(state.challenge, isNull);
      expect(state.identifier, 'person@example.test');
      expect(state.errorCode, code);

      controller.retry();
      state = container.read(accountControllerProvider);
      expect(state.uiState, AccountUiState.enterIdentifier);
      expect(state.identifier, 'person@example.test');
      expect(state.errorCode, isNull);
    });
  }

  for (final code in const [
    'AUTH_VERIFICATION_INVALID',
    'AUTH_MERGE_REPLAY_MISMATCH',
  ]) {
    test('$code after verification requires a new challenge', () async {
      final repository = _RecoveryAccountRepository(mergeErrorCode: code);
      final container = _container(repository);
      addTearDown(container.dispose);
      final controller = container.read(accountControllerProvider.notifier);

      controller.setIdentifier('person@example.test');
      await controller.requestOtp();
      await controller.verifyAndMerge('123456');

      final state = container.read(accountControllerProvider);
      expect(state.uiState, AccountUiState.error);
      expect(state.challenge, isNull);
      expect(state.identifier, 'person@example.test');
      expect(state.errorCode, code);
    });
  }

  for (final failurePhase in const ['verification', 'merge']) {
    test(
      '$failurePhase transport uncertainty requires a new challenge',
      () async {
        final repository = _RecoveryAccountRepository(
          verificationTransport: failurePhase == 'verification',
          mergeTransport: failurePhase == 'merge',
        );
        final container = _container(repository);
        addTearDown(container.dispose);
        final controller = container.read(accountControllerProvider.notifier);

        controller.setIdentifier('person@example.test');
        await controller.requestOtp();
        await controller.verifyAndMerge('123456');

        final state = container.read(accountControllerProvider);
        expect(state.uiState, AccountUiState.error);
        expect(state.challenge, isNull);
        expect(state.identifier, 'person@example.test');
        expect(state.errorCode, 'NETWORK_TIMEOUT');
      },
    );
  }

  test('controller rejects incomplete or non-numeric codes locally', () async {
    final repository = _RecoveryAccountRepository();
    final container = _container(repository);
    addTearDown(container.dispose);
    final controller = container.read(accountControllerProvider.notifier);

    controller.setIdentifier('person@example.test');
    await controller.requestOtp();
    await controller.verifyAndMerge('12345');
    await controller.verifyAndMerge('12a456');

    expect(repository.verifyCalls, 0);
    expect(
      container.read(accountControllerProvider).uiState,
      AccountUiState.enterCode,
    );
  });

  for (final locale in const [Locale('tr', 'TR'), Locale('en', 'US')]) {
    testWidgets(
      'buttons enforce visible minimum input and invalid code recovers in ${locale.languageCode}',
      (tester) async {
        final repository = _RecoveryAccountRepository(
          verifyErrorCode: 'AUTH_OTP_INVALID',
        );
        await _pumpAccount(tester, locale: locale, repository: repository);

        expect(_button(tester, 'account-request-otp').onPressed, isNull);
        await tester.enterText(
          find.byKey(const ValueKey('account-identifier')),
          'person@example.test',
        );
        await tester.pump();
        expect(_button(tester, 'account-request-otp').onPressed, isNotNull);

        await tester.tap(find.byKey(const ValueKey('account-request-otp')));
        await tester.pumpAndSettle();
        expect(find.byKey(const ValueKey('account-otp-code')), findsOneWidget);
        expect(_button(tester, 'account-verify-merge').onPressed, isNull);

        await tester.enterText(
          find.byKey(const ValueKey('account-otp-code')),
          '12345',
        );
        await tester.pump();
        expect(_button(tester, 'account-verify-merge').onPressed, isNull);
        await tester.enterText(
          find.byKey(const ValueKey('account-otp-code')),
          '123456',
        );
        await tester.pump();
        final codeField = tester.widget<TextField>(
          find.byKey(const ValueKey('account-otp-code')),
        );
        expect(codeField.controller!.text, '123456');
        expect(_button(tester, 'account-verify-merge').onPressed, isNotNull);

        await tester.ensureVisible(
          find.byKey(const ValueKey('account-verify-merge')),
        );
        await tester.tap(find.byKey(const ValueKey('account-verify-merge')));
        await tester.pumpAndSettle();

        expect(find.byKey(const ValueKey('account-code-surface')), findsOneWidget);
        expect(find.byKey(const ValueKey('account-error')), findsOneWidget);
        expect(find.textContaining('AUTH_OTP_INVALID'), findsNothing);
        expect(
          find.textContaining(
            locale.languageCode == 'tr'
                ? 'Bu kod doğru değil.'
                : "That code wasn't correct.",
          ),
          findsOneWidget,
        );

        repository.verifyErrorCode = null;
        await tester.enterText(
          find.byKey(const ValueKey('account-otp-code')),
          '654321',
        );
        await tester.pump();
        expect(find.byKey(const ValueKey('account-error')), findsNothing);
        await tester.ensureVisible(
          find.byKey(const ValueKey('account-verify-merge')),
        );
        await tester.tap(find.byKey(const ValueKey('account-verify-merge')));
        await tester.pumpAndSettle();
        expect(
          find.byKey(const ValueKey('account-complete-surface')),
          findsOneWidget,
        );
        expect(tester.takeException(), isNull);
      },
    );
  }

  testWidgets('Product Preview incorrect code stays recoverable', (
    tester,
  ) async {
    await _pumpAccount(
      tester,
      locale: const Locale('en', 'US'),
      repository: PreviewAccountRepository(),
    );
    await tester.enterText(
      find.byKey(const ValueKey('account-identifier')),
      'preview@example.test',
    );
    await tester.tap(find.byKey(const ValueKey('account-request-otp')));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const ValueKey('account-otp-code')),
      '000000',
    );
    await tester.ensureVisible(
      find.byKey(const ValueKey('account-verify-merge')),
    );
    await tester.tap(find.byKey(const ValueKey('account-verify-merge')));
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('account-code-surface')), findsOneWidget);
    expect(find.textContaining("That code wasn't correct."), findsOneWidget);
    expect(find.textContaining('PREVIEW_OTP_INVALID'), findsNothing);
    expect(tester.takeException(), isNull);
  });

  test('known and unknown failures never expose raw internal codes', () {
    final tr = KefeStrings(const Locale('tr', 'TR'));
    final en = KefeStrings(const Locale('en', 'US'));
    for (final code in const [
      'AUTH_OTP_INVALID',
      'AUTH_OTP_EXPIRED',
      'AUTH_OTP_ATTEMPTS_EXCEEDED',
      'AUTH_OTP_DELIVERY_UNAVAILABLE',
      'AUTH_OTP_DELIVERY_REJECTED',
      'AUTH_RATE_LIMITED',
      'AUTH_VERIFICATION_INVALID',
      'AUTH_MERGE_REPLAY_MISMATCH',
      'UNEXPECTED_INTERNAL_CODE',
    ]) {
      expect(tr.accountFailure(code), isNot(contains(code)));
      expect(en.accountFailure(code), isNot(contains(code)));
    }
  });

  test('executable contract guards recovery and Preview boundaries', () {
    final contract =
        jsonDecode(
              File(
                '../../docs/contracts/account-conversion-validation-recovery.v1.json',
              ).readAsStringSync(),
            )
            as Map<String, Object?>;
    final local = contract['local_validation']! as Map<String, Object?>;
    final same =
        contract['same_challenge_recovery']! as Map<String, Object?>;
    final fresh = contract['new_challenge_required']! as Map<String, Object?>;
    final presentation = contract['presentation']! as Map<String, Object?>;
    final preview = contract['preview']! as Map<String, Object?>;
    final preserved = contract['preserved']! as Map<String, Object?>;
    final screenSource = File(
      'lib/features/account/presentation/account_conversion_screen.dart',
    ).readAsStringSync();
    final controllerSource = File(
      'lib/features/account/application/account_controller.dart',
    ).readAsStringSync();

    expect(local['otp_digits_only'], isTrue);
    expect(local['server_validation_authoritative'], isTrue);
    expect(same['error_codes'], ['AUTH_OTP_INVALID']);
    expect(same['challenge_preserved'], isTrue);
    expect(fresh['challenge_cleared'], isTrue);
    expect(fresh['verification_or_merge_transport_failure'], isTrue);
    expect(presentation['raw_error_code_visible'], isFalse);
    expect(preview['uncaught_state_error_allowed'], isFalse);
    expect(preserved['optional_guest_continuation'], isTrue);
    expect(preserved['channels'], ['EMAIL', 'SMS']);
    expect(preserved['api_changed'], isFalse);
    expect(screenSource, contains('FilteringTextInputFormatter.digitsOnly'));
    expect(screenSource, contains("ValueKey('account-error-retry')"));
    expect(controllerSource, contains("code == 'AUTH_OTP_INVALID'"));
  });
}

ProviderContainer _container(AccountRepository repository) => ProviderContainer(
  overrides: [accountRepositoryProvider.overrideWithValue(repository)],
);

FilledButton _button(WidgetTester tester, String key) =>
    tester.widget<FilledButton>(find.byKey(ValueKey(key)));

Future<void> _pumpAccount(
  WidgetTester tester, {
  required Locale locale,
  required AccountRepository repository,
}) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [accountRepositoryProvider.overrideWithValue(repository)],
      child: MaterialApp(
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
        home: const AccountConversionScreen(),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

class _RecoveryAccountRepository implements AccountRepository {
  _RecoveryAccountRepository({
    this.verifyErrorCode,
    this.mergeErrorCode,
    this.verificationTransport = false,
    this.mergeTransport = false,
  });

  String? verifyErrorCode;
  final String? mergeErrorCode;
  final bool verificationTransport;
  final bool mergeTransport;
  int verifyCalls = 0;

  @override
  Future<OtpChallenge> requestOtp({
    required String channel,
    required String identifier,
  }) async => OtpChallenge(
    id: 'challenge-1',
    destinationHint: 'p***@example.test',
    expiresAt: DateTime.utc(2026, 8, 31, 5),
  );

  @override
  Future<OtpVerification> verifyOtp({
    required String challengeId,
    required String code,
  }) async {
    verifyCalls += 1;
    if (verificationTransport) {
      throw const ClientTransportFailure(code: 'NETWORK_TIMEOUT');
    }
    final errorCode = verifyErrorCode;
    if (errorCode != null) throw ApiFailure(errorCode, 422);
    return OtpVerification(
      token: 'verification-token',
      expiresAt: DateTime.utc(2026, 8, 31, 5),
    );
  }

  @override
  Future<AccountConversion> mergeGuest({
    required String verificationToken,
  }) async {
    if (mergeTransport) {
      throw const ClientTransportFailure(code: 'NETWORK_TIMEOUT');
    }
    final errorCode = mergeErrorCode;
    if (errorCode != null) throw ApiFailure(errorCode, 409);
    return const AccountConversion(
      actorId: 'account-actor',
      mergedExistingHistory: true,
    );
  }
}
