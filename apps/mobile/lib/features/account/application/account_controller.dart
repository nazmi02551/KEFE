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
  merging,
  complete,
  error,
}

enum AccountFailurePhase { requestOtp, verifyOtp, mergeGuest }

class AccountState {
  const AccountState({
    this.uiState = AccountUiState.enterIdentifier,
    this.channel = 'EMAIL',
    this.identifier = '',
    this.challenge,
    this.actorId,
    this.mergedExistingHistory = false,
    this.errorCode,
    this.failurePhase,
  });

  final AccountUiState uiState;
  final String channel;
  final String identifier;
  final OtpChallenge? challenge;
  final String? actorId;
  final bool mergedExistingHistory;
  final String? errorCode;
  final AccountFailurePhase? failurePhase;

  AccountState copyWith({
    AccountUiState? uiState,
    String? channel,
    String? identifier,
    OtpChallenge? challenge,
    String? actorId,
    bool? mergedExistingHistory,
    String? errorCode,
    AccountFailurePhase? failurePhase,
    bool clearChallenge = false,
    bool clearError = false,
    bool clearFailure = false,
  }) => AccountState(
    uiState: uiState ?? this.uiState,
    channel: channel ?? this.channel,
    identifier: identifier ?? this.identifier,
    challenge: clearChallenge ? null : challenge ?? this.challenge,
    actorId: actorId ?? this.actorId,
    mergedExistingHistory: mergedExistingHistory ?? this.mergedExistingHistory,
    errorCode: clearError ? null : errorCode ?? this.errorCode,
    failurePhase: clearFailure
        ? null
        : failurePhase ?? this.failurePhase,
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

  OtpVerification? _pendingVerification;

  bool get _isBusy =>
      state.uiState == AccountUiState.requesting ||
      state.uiState == AccountUiState.verifying ||
      state.uiState == AccountUiState.merging;

  @override
  AccountState build() => const AccountState();

  void setChannel(String value) {
    if (_isBusy || (value != 'EMAIL' && value != 'SMS')) return;
    _pendingVerification = null;
    state = state.copyWith(
      uiState: AccountUiState.enterIdentifier,
      channel: value,
      clearChallenge: true,
      clearError: true,
      clearFailure: true,
    );
  }

  void setIdentifier(String value) {
    if (_isBusy) return;
    _pendingVerification = null;
    state = state.copyWith(
      uiState: AccountUiState.enterIdentifier,
      identifier: value,
      clearChallenge: true,
      clearError: true,
      clearFailure: true,
    );
  }

  Future<void> requestOtp() async {
    if (_isBusy || state.identifier.trim().isEmpty) return;
    _pendingVerification = null;
    state = state.copyWith(
      uiState: AccountUiState.requesting,
      clearChallenge: true,
      clearError: true,
      clearFailure: true,
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
        clearFailure: true,
      );
    } on ApiFailure catch (error) {
      _fail(AccountFailurePhase.requestOtp, error.code);
    } on ClientTransportFailure catch (error) {
      _fail(AccountFailurePhase.requestOtp, error.code);
    }
  }

  Future<void> verifyAndMerge(String code) async {
    if (_isBusy) return;
    final challenge = state.challenge;
    if (challenge == null || code.trim().length != 6) return;

    _pendingVerification = null;
    state = state.copyWith(
      uiState: AccountUiState.verifying,
      clearError: true,
      clearFailure: true,
    );

    try {
      _pendingVerification = await _repository.verifyOtp(
        challengeId: challenge.id,
        code: code.trim(),
      );
    } on ApiFailure catch (error) {
      _fail(AccountFailurePhase.verifyOtp, error.code);
      return;
    } on ClientTransportFailure catch (error) {
      _fail(AccountFailurePhase.verifyOtp, error.code);
      return;
    }

    state = state.copyWith(
      uiState: AccountUiState.merging,
      clearError: true,
      clearFailure: true,
    );
    await _mergePendingVerification();
  }

  Future<void> retry() async {
    if (_isBusy) return;

    switch (state.failurePhase) {
      case AccountFailurePhase.requestOtp:
        await requestOtp();
      case AccountFailurePhase.verifyOtp:
        state = state.copyWith(
          uiState: AccountUiState.enterCode,
          clearError: true,
          clearFailure: true,
        );
      case AccountFailurePhase.mergeGuest:
        if (_pendingVerification == null) {
          state = state.copyWith(
            uiState: AccountUiState.enterCode,
            clearError: true,
            clearFailure: true,
          );
          return;
        }
        state = state.copyWith(
          uiState: AccountUiState.merging,
          clearError: true,
          clearFailure: true,
        );
        await _mergePendingVerification();
      case null:
        _pendingVerification = null;
        state = AccountState(
          channel: state.channel,
          identifier: state.identifier,
        );
    }
  }

  Future<void> _mergePendingVerification() async {
    final verification = _pendingVerification;
    if (verification == null) {
      state = state.copyWith(
        uiState: AccountUiState.enterCode,
        clearError: true,
        clearFailure: true,
      );
      return;
    }

    try {
      final conversion = await _repository.mergeGuest(
        verificationToken: verification.token,
      );
      _pendingVerification = null;
      state = state.copyWith(
        uiState: AccountUiState.complete,
        actorId: conversion.actorId,
        mergedExistingHistory: conversion.mergedExistingHistory,
        clearError: true,
        clearFailure: true,
      );
    } on ApiFailure catch (error) {
      _fail(AccountFailurePhase.mergeGuest, error.code);
    } on ClientTransportFailure catch (error) {
      _fail(AccountFailurePhase.mergeGuest, error.code);
    }
  }

  void _fail(AccountFailurePhase phase, String code) {
    state = state.copyWith(
      uiState: AccountUiState.error,
      errorCode: code,
      failurePhase: phase,
    );
  }
}
