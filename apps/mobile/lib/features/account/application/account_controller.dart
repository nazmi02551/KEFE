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

  bool get canRequestOtp =>
      identifier.trim().isNotEmpty && uiState != AccountUiState.requesting;

  bool canVerifyCode(String code) {
    final clean = code.trim();
    return clean.length == 6 &&
        RegExp(r'^[0-9]{6}$').hasMatch(clean) &&
        uiState != AccountUiState.verifying;
  }

  AccountState copyWith({
    AccountUiState? uiState,
    String? channel,
    String? identifier,
    OtpChallenge? challenge,
    String? actorId,
    bool? mergedExistingHistory,
    String? errorCode,
    bool clearError = false,
  }) => AccountState(
    uiState: uiState ?? this.uiState,
    channel: channel ?? this.channel,
    identifier: identifier ?? this.identifier,
    challenge: challenge ?? this.challenge,
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
    final cleanIdentifier = state.identifier.trim();
    if (cleanIdentifier.isEmpty) return;
    state = state.copyWith(
      uiState: AccountUiState.requesting,
      clearError: true,
    );
    try {
      final challenge = await _repository.requestOtp(
        channel: state.channel,
        identifier: cleanIdentifier,
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
    final cleanCode = code.trim();
    if (challenge == null ||
        cleanCode.length != 6 ||
        !RegExp(r'^[0-9]{6}$').hasMatch(cleanCode)) {
      return;
    }
    state = state.copyWith(uiState: AccountUiState.verifying, clearError: true);
    try {
      final verification = await _repository.verifyOtp(
        challengeId: challenge.id,
        code: cleanCode,
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
      if (error.code == 'AUTH_OTP_INVALID') {
        state = state.copyWith(
          uiState: AccountUiState.enterCode,
          errorCode: error.code,
        );
      } else {
        state = state.copyWith(
          uiState: AccountUiState.error,
          errorCode: error.code,
          challenge: null,
        );
      }
    } on ClientTransportFailure catch (error) {
      state = state.copyWith(
        uiState: AccountUiState.error,
        errorCode: error.code,
      );
    }
  }

  void retry() {
    if (state.uiState == AccountUiState.enterCode) {
      state = state.copyWith(clearError: true);
    } else {
      state = AccountState(channel: state.channel, identifier: state.identifier);
    }
  }

  void restartChallenge() {
    state = AccountState(channel: state.channel, identifier: state.identifier);
  }
}
