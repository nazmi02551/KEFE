abstract interface class AccountRepository {
  Future<OtpChallenge> requestOtp({
    required String channel,
    required String identifier,
  });

  Future<OtpVerification> verifyOtp({
    required String challengeId,
    required String code,
  });

  Future<AccountConversion> mergeGuest({required String verificationToken});
}

class OtpChallenge {
  const OtpChallenge({
    required this.id,
    required this.destinationHint,
    required this.expiresAt,
  });

  final String id;
  final String destinationHint;
  final DateTime expiresAt;
}

class OtpVerification {
  const OtpVerification({required this.token, required this.expiresAt});

  final String token;
  final DateTime expiresAt;
}

class AccountConversion {
  const AccountConversion({
    required this.actorId,
    required this.mergedExistingHistory,
  });

  final String actorId;
  final bool mergedExistingHistory;
}
