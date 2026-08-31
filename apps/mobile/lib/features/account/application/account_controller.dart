import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../decision/application/decision_controller.dart';
import '../../decision/data/decision_repository.dart';
import '../../decision/data/http_decision_repository.dart';
import '../data/account_repository.dart';
import '../data/http_account_repository.dart';

enum AccountUiState {
  enterIdentifier,
  requesting,
  enterCode,
  verifying,
  complete,
  error,
}

class AccountState {
  const AccountState({
    this.uiState = AccountUiState.enterIdentifier,
    this.channel = 'EMAIL',
    this.identifier = '',
    this.challenge,
    this.actorId,
    this.mergedExistingHistory = false,
    this.errorCode,
  });

  final AccountUiState uiState;
  final String channel;
  final String identifier;
  final OtpChallenge? challenge;
  final String? actorId;
  final bool mergedExistingHistory;
  final String? errorCode;

  AccountState copyWith({
    AccountUiState? uiState,
    String? channel,
    String? identifier,
    OtpChallenge? challenge,
    String? actorId,
    bool? mergedExistingHistory,
    String? errorCode,
    bool clearError = false,
    bool clearChallenge = false,
  }) => AccountState(
    uiState: uiState ?? this.uiState,
    channel: channel ?? this.channel,
    identifier: identifier ?? this.identifier,
    challenge: clearChallenge ? null : challenge ?? this.challenge,
    actorId: actorId ?? this.actorId,
    mergedExistingHistory: mergedExistingHistory ?? this.mergedExistingHistory,
    errorCode: clearError ? null : errorCode ?? this.errorCode,
  );
}

final accountRepositoryProvider = Provider<AccountRepository>((ref) {
  return HttpAccountRepository(
    config: ref.watch(appConfigProvider),
    client: ref.watch(httpClientProvider),
    credentialStore: ref.watch(credentialStoreProvider),
  );
});

final accountControllerProvider =
    NotifierProvider<AccountController, AccountState>(AccountController.new);

class AccountController extends Notifier<AccountState> {
  AccountRepository get _repository => ref.read(accountRepositoryProvider);

  @override
  AccountState build() => const AccountState();

  void setChannel(String value) {
    if (value != 'EMAIL' && value != 'SMS') return;
    state = state.copyWith(channel: value, clearError: true);
  }

  void setIdentifier(String value) {
    state = state.copyWith(identifier: value, clearError: true);
  }

  Future<void> requestOtp() async {
    if (state.identifier.trim().isEmpty) return;
    state = state.copyWith(
      uiState: AccountUiState.requesting,
      clearError: true,
    );
    try {
      final challenge = await _repository.requestOtp(
        channel: state.channel,
        identifier: state.identifier.trim(),
      );
      state = state.copyWith(
        uiState: AccountUiState.enterCode,
        challenge: challenge,
        clearError: true,
      );
    } on ApiFailure catch (error) {
      state = state.copyWith(
        uiState: AccountUiState.error,
        errorCode: error.code,
      );
    } on ClientTransportFailure catch (error) {
      state = state.copyWith(
        uiState: AccountUiState.error,
        errorCode: error.code,
      );
    }
  }

  Future<void> verifyAndMerge(String code) async {
    final challenge = state.challenge;
    final normalizedCode = code.trim();
    if (challenge == null || !RegExp(r'^\d{6}$').hasMatch(normalizedCode)) {
      return;
    }
    state = state.copyWith(uiState: AccountUiState.verifying, clearError: true);
    try {
      final verification = await _repository.verifyOtp(
        challengeId: challenge.id,
        code: normalizedCode,
      );
      final conversion = await _repository.mergeGuest(
        verificationToken: verification.token,
      );
      state = state.copyWith(
        uiState: AccountUiState.complete,
        actorId: conversion.actorId,
        mergedExistingHistory: conversion.mergedExistingHistory,
        clearError: true,
      );
    } on ApiFailure catch (error) {
      _recoverFromVerificationFailure(error.code);
    } on ClientTransportFailure catch (error) {
      _recoverFromVerificationFailure(error.code);
    }
  }

  void clearError() {
    if (state.errorCode == null ||
        state.uiState == AccountUiState.requesting ||
        state.uiState == AccountUiState.verifying) {
      return;
    }
    state = state.copyWith(clearError: true);
  }

  void retry() {
    if (state.uiState == AccountUiState.enterCode && state.challenge != null) {
      clearError();
      return;
    }
    state = AccountState(channel: state.channel, identifier: state.identifier);
  }

  void _recoverFromVerificationFailure(String code) {
    final retrySameChallenge = code == 'AUTH_OTP_INVALID';
    state = state.copyWith(
      uiState: retrySameChallenge
          ? AccountUiState.enterCode
          : AccountUiState.error,
      errorCode: code,
      clearChallenge: !retrySameChallenge,
    );
  }
}
