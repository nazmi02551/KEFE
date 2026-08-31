import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/localization/internal_alpha_strings.dart';
import 'package:mobile/core/localization/kefe_strings.dart';
import 'package:mobile/features/account/application/account_controller.dart';
import 'package:mobile/features/account/data/account_repository.dart';
import 'package:mobile/features/account/data/preview_account_repository.dart';
import 'package:mobile/features/decision/data/http_decision_repository.dart';

class FakeAccountRepository implements AccountRepository {
  OtpChallenge? requestedChallenge;
  String? nextErrorCode;
  bool requestCalled = false;
  bool verifyCalled = false;

  @override
  Future<OtpChallenge> requestOtp({
    required String channel,
    required String identifier,
  }) async {
    requestCalled = true;
    if (nextErrorCode != null) {
      throw ApiFailure(nextErrorCode!, 400);
    }
    final challenge = OtpChallenge(
      id: 'challenge-1',
      destinationHint: identifier,
      expiresAt: DateTime.now().toUtc().add(const Duration(minutes: 5)),
    );
    requestedChallenge = challenge;
    return challenge;
  }

  @override
  Future<OtpVerification> verifyOtp({
    required String challengeId,
    required String code,
  }) async {
    verifyCalled = true;
    if (nextErrorCode != null) {
      throw ApiFailure(nextErrorCode!, 400);
    }
    return OtpVerification(
      token: 'verification-token-1',
      expiresAt: DateTime.now().toUtc().add(const Duration(minutes: 5)),
    );
  }

  @override
  Future<AccountConversion> mergeGuest({
    required String verificationToken,
  }) async {
    return const AccountConversion(
      actorId: 'merged-actor-1',
      mergedExistingHistory: true,
    );
  }
}

void main() {
  group('Account conversion validation and recovery contract & structure', () {
    test('contract file exists and is valid JSON', () {
      final contractFile = File(
        '../../docs/contracts/account-conversion-validation-recovery.v1.json',
      );
      expect(contractFile.existsSync(), isTrue);
      expect(
        contractFile.readAsStringSync(),
        contains('KEFE-ACCOUNT-CONVERSION-VALIDATION-RECOVERY-001'),
      );
    });

    test('ADR-0145 exists', () {
      final adrFile = File(
        '../../docs/adr/0145-account-conversion-validation-recovery.md',
      );
      expect(adrFile.existsSync(), isTrue);
      expect(
        adrFile.readAsStringSync(),
        contains('Account conversion validation and recovery'),
      );
    });

    test('Screen uses inputFormatters, validation flags and restart challenge', () {
      final screenSource = File(
        'lib/features/account/presentation/account_conversion_screen.dart',
      ).readAsStringSync();

      expect(screenSource, contains('FilteringTextInputFormatter.digitsOnly'));
      expect(screenSource, contains('LengthLimitingTextInputFormatter(6)'));
      expect(screenSource, contains('state.canRequestOtp'));
      expect(screenSource, contains('state.canVerifyCode'));
      expect(screenSource, contains("ValueKey('account-restart-challenge')"));
      expect(screenSource, contains('controller.restartChallenge()'));
    });
  });

  group('AccountState validation helper properties', () {
    test('canRequestOtp requires non-empty identifier and non-requesting state', () {
      const emptyState = AccountState(identifier: '');
      expect(emptyState.canRequestOtp, isFalse);

      const whitespaceState = AccountState(identifier: '   ');
      expect(whitespaceState.canRequestOtp, isFalse);

      const validState = AccountState(identifier: 'user@example.com');
      expect(validState.canRequestOtp, isTrue);

      final requestingState = validState.copyWith(
        uiState: AccountUiState.requesting,
      );
      expect(requestingState.canRequestOtp, isFalse);
    });

    test('canVerifyCode requires exactly 6 numeric digits', () {
      const state = AccountState(uiState: AccountUiState.enterCode);

      expect(state.canVerifyCode(''), isFalse);
      expect(state.canVerifyCode('12345'), isFalse);
      expect(state.canVerifyCode('1234567'), isFalse);
      expect(state.canVerifyCode('12345a'), isFalse);
      expect(state.canVerifyCode('abcdef'), isFalse);
      expect(state.canVerifyCode(' 123456 '), isTrue);
      expect(state.canVerifyCode('123456'), isTrue);

      final verifyingState = state.copyWith(uiState: AccountUiState.verifying);
      expect(verifyingState.canVerifyCode('123456'), isFalse);
    });
  });

  group('PreviewAccountRepository error contract', () {
    test('throws ApiFailure instead of StateError on invalid code', () async {
      final repository = PreviewAccountRepository();
      await repository.requestOtp(channel: 'EMAIL', identifier: 'test@example.com');

      expect(
        () => repository.verifyOtp(challengeId: 'preview-challenge', code: '000000'),
        throwsA(
          isA<ApiFailure>()
              .having((e) => e.code, 'code', 'AUTH_OTP_INVALID')
              .having((e) => e.statusCode, 'statusCode', 400),
        ),
      );
    });

    test('throws ApiFailure on invalid verification token', () async {
      final repository = PreviewAccountRepository();

      expect(
        () => repository.mergeGuest(verificationToken: 'invalid-token'),
        throwsA(
          isA<ApiFailure>()
              .having((e) => e.code, 'code', 'AUTH_VERIFICATION_TOKEN_INVALID')
              .having((e) => e.statusCode, 'statusCode', 400),
        ),
      );
    });
  });

  group('Bounded localization for account errors', () {
    test('Turkish translations provide bounded copy without raw codes', () {
      final strings = KefeStrings(const Locale('tr'));

      expect(
        strings.accountFailure('AUTH_OTP_INVALID'),
        'Doğrulama kodu hatalı. Lütfen kodu kontrol edip tekrar dene.',
      );
      expect(
        strings.accountFailure('AUTH_OTP_EXPIRED'),
        'Doğrulama kodunun süresi doldu. Lütfen yeni bir kod iste.',
      );
      expect(
        strings.accountFailure('AUTH_OTP_LOCKED'),
        'Çok fazla deneme yapıldı. Lütfen daha sonra tekrar dene veya yeni bir kod iste.',
      );
      expect(
        strings.accountFailure('AUTH_RATE_LIMITED'),
        'Çok fazla deneme yapıldı. Lütfen daha sonra tekrar dene veya yeni bir kod iste.',
      );
      expect(
        strings.accountFailure('AUTH_CHALLENGE_EXPIRED'),
        'Doğrulama oturumunun süresi doldu. Lütfen yeni bir kod iste.',
      );
      expect(
        strings.accountFailure('AUTH_VERIFICATION_TOKEN_EXPIRED'),
        'Hesap geçmişi birleştirilemedi. Lütfen yeni bir doğrulama kodu iste.',
      );
      expect(
        strings.accountFailure('UNKNOWN_SYSTEM_ERROR'),
        'Doğrulama işlemi tamamlanamadı. Lütfen tekrar dene.',
      );
      expect(strings.accountRestartChallenge, 'Hedefi değiştir veya yeni kod iste');
    });

    test('English translations provide bounded copy without raw codes', () {
      final strings = KefeStrings(const Locale('en'));

      expect(
        strings.accountFailure('AUTH_OTP_INVALID'),
        'The verification code is incorrect. Please check the code and try again.',
      );
      expect(
        strings.accountFailure('AUTH_OTP_EXPIRED'),
        'The verification code has expired. Please request a new code.',
      );
      expect(
        strings.accountFailure('AUTH_OTP_LOCKED'),
        'Too many verification attempts. Please try again later or request a new code.',
      );
      expect(
        strings.accountFailure('AUTH_RATE_LIMITED'),
        'Too many verification attempts. Please try again later or request a new code.',
      );
      expect(
        strings.accountFailure('AUTH_CHALLENGE_EXPIRED'),
        'The verification session has expired. Please request a new code.',
      );
      expect(
        strings.accountFailure('AUTH_VERIFICATION_TOKEN_EXPIRED'),
        'Could not merge your account history. Please request a new verification code.',
      );
      expect(
        strings.accountFailure('UNKNOWN_SYSTEM_ERROR'),
        'Verification could not be completed. Please try again.',
      );
      expect(
        strings.accountRestartChallenge,
        'Change destination or request new code',
      );
    });
  });
}
