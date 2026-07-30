import 'account_repository.dart';

/// Internal Product Preview adapter only. This never represents real OTP delivery.
class PreviewAccountRepository implements AccountRepository {
  static const testCode = '123456';

  String? _challengeId;

  @override
  Future<OtpChallenge> requestOtp({
    required String channel,
    required String identifier,
  }) async {
    _challengeId = 'preview-challenge';
    return OtpChallenge(
      id: _challengeId!,
      destinationHint: 'Product Preview · code $testCode',
      expiresAt: DateTime.now().toUtc().add(const Duration(minutes: 10)),
    );
  }

  @override
  Future<OtpVerification> verifyOtp({
    required String challengeId,
    required String code,
  }) async {
    if (challengeId != _challengeId || code != testCode) {
      throw StateError('PREVIEW_OTP_INVALID');
    }
    return OtpVerification(
      token: 'preview-verification-token',
      expiresAt: DateTime.now().toUtc().add(const Duration(minutes: 10)),
    );
  }

  @override
  Future<AccountConversion> mergeGuest({required String verificationToken}) async {
    if (verificationToken != 'preview-verification-token') {
      throw StateError('PREVIEW_VERIFICATION_INVALID');
    }
    return const AccountConversion(
      actorId: 'preview-account-actor',
      mergedExistingHistory: true,
    );
  }
}
