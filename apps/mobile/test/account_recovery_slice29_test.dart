import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/account/application/account_controller.dart';
import 'package:kefe_mobile/features/account/data/account_repository.dart';
import 'package:kefe_mobile/features/account/presentation/account_conversion_screen.dart';
import 'package:kefe_mobile/features/decision/data/decision_repository.dart';

void main() {
  test('Slice 29 contract locks phase-aware recovery and token privacy', () {
    final contract =
        jsonDecode(
              File(
                '../../docs/contracts/account-recovery-slice29.v1.json',
              ).readAsStringSync(),
            )
            as Map<String, dynamic>;

    expect(contract['contract'], 'account-recovery-slice29');
    expect(contract['scope']['repository_interface_change'], isFalse);
    expect(contract['scope']['api_change'], isFalse);
    expect(contract['operations']['request_otp']['retry_action'], 'requestOtp');
    expect(
      contract['operations']['verify_otp']['retry_action'],
      'resumeCodeEntry',
    );
    expect(
      contract['operations']['merge_guest']['retry_action'],
      'mergeGuestWithPrivatePendingVerification',
    );
    expect(contract['security']['verification_token_in_account_state'], isFalse);
    expect(contract['security']['verification_token_persisted'], isFalse);
    expect(contract['security']['verification_token_logged'], isFalse);
    expect(contract['guards']['duplicate_request_ignored'], isTrue);
    expect(contract['guards']['duplicate_verify_ignored'], isTrue);
    expect(contract['guards']['duplicate_merge_ignored'], isTrue);
    expect(contract['preserved']['signal_in_scope'], isFalse);
    expect(contract['preserved']['impact_in_scope'], isFalse);
  });

  test('verified token stays out of AccountState and presentation', () {
    final controllerSource = File(
      'lib/features/account/application/account_controller.dart',
    ).readAsStringSync();
    final stateSource = controllerSource.substring(
      controllerSource.indexOf('class AccountState'),
      controllerSource.indexOf('final accountRepositoryProvider'),
    );
    final screenSource = File(
      'lib/features/account/presentation/account_conversion_screen.dart',
    ).readAsStringSync();

    expect(stateSource, isNot(contains('OtpVerification')));
    expect(stateSource, isNot(contains('verificationToken')));
    expect(screenSource, isNot(contains('verificationToken')));
    expect(controllerSource, contains('OtpVerification? _pendingVerification'));
    expect(controllerSource, isNot(contains('print(')));
    expect(controllerSource, isNot(contains('log(')));
  });

  test('request failure retry preserves identifier and repeats request', () async {
    final repository = _ControllableAccountRepository()..requestFailures = 1;
    final container = _container(repository);
    addTearDown(container.dispose);
    final controller = container.read(accountControllerProvider.notifier);

    controller.setIdentifier('person@example.com');
    await controller.requestOtp();

    expect(repository.requestCalls, 1);
    expect(container.read(accountControllerProvider).uiState, AccountUiState.error);
    expect(
      container.read(accountControllerProvider).failurePhase,
      AccountFailurePhase.requestOtp,
    );
    expect(
      container.read(accountControllerProvider).identifier,
      'person@example.com',
    );

    await controller.retry();

    final state = container.read(accountControllerProvider);
    expect(repository.requestCalls, 2);
    expect(state.uiState, AccountUiState.enterCode);
    expect(state.identifier, 'person@example.com');
    expect(state.challenge?.id, 'challenge-1');
  });

  test('verification failure keeps challenge and retry resumes code entry', () async {
    final repository = _ControllableAccountRepository()..verifyFailures = 1;
    final container = _container(repository);
    addTearDown(container.dispose);
    final controller = container.read(accountControllerProvider.notifier);

    controller.setIdentifier('person@example.com');
    await controller.requestOtp();
    final challenge = container.read(accountControllerProvider).challenge;
    await controller.verifyAndMerge('123456');

    expect(repository.requestCalls, 1);
    expect(repository.verifyCalls, 1);
    expect(repository.mergeCalls, 0);
    expect(
      container.read(accountControllerProvider).failurePhase,
      AccountFailurePhase.verifyOtp,
    );
    expect(container.read(accountControllerProvider).challenge, same(challenge));

    await controller.retry();

    final state = container.read(accountControllerProvider);
    expect(state.uiState, AccountUiState.enterCode);
    expect(state.challenge, same(challenge));
    expect(repository.requestCalls, 1);
    expect(repository.verifyCalls, 1);
    expect(repository.mergeCalls, 0);
  });

  test('merge failure retry repeats only merge with verified context', () async {
    final repository = _ControllableAccountRepository()..mergeFailures = 1;
    final container = _container(repository);
    addTearDown(container.dispose);
    final controller = container.read(accountControllerProvider.notifier);

    controller.setIdentifier('person@example.com');
    await controller.requestOtp();
    await controller.verifyAndMerge('123456');

    expect(repository.requestCalls, 1);
    expect(repository.verifyCalls, 1);
    expect(repository.mergeCalls, 1);
    expect(repository.mergeTokens, ['verified-token']);
    expect(
      container.read(accountControllerProvider).failurePhase,
      AccountFailurePhase.mergeGuest,
    );

    await controller.retry();

    final state = container.read(accountControllerProvider);
    expect(repository.requestCalls, 1);
    expect(repository.verifyCalls, 1);
    expect(repository.mergeCalls, 2);
    expect(repository.mergeTokens, ['verified-token', 'verified-token']);
    expect(state.uiState, AccountUiState.complete);
    expect(state.actorId, 'actor-1');
    expect(state.mergedExistingHistory, isTrue);
  });

  test('duplicate request verify and merge actions are guarded', () async {
    final repository = _ControllableAccountRepository();
    final container = _container(repository);
    addTearDown(container.dispose);
    final controller = container.read(accountControllerProvider.notifier);

    controller.setIdentifier('person@example.com');
    repository.requestGate = Completer<OtpChallenge>();
    final request = controller.requestOtp();
    await Future<void>.delayed(Duration.zero);
    await controller.requestOtp();
    expect(repository.requestCalls, 1);
    repository.requestGate!.complete(repository.challenge);
    await request;

    repository.verifyGate = Completer<OtpVerification>();
    final verify = controller.verifyAndMerge('123456');
    await Future<void>.delayed(Duration.zero);
    await controller.verifyAndMerge('123456');
    expect(repository.verifyCalls, 1);
    repository.verifyGate!.complete(repository.verification);

    repository.mergeGate = Completer<AccountConversion>();
    await Future<void>.delayed(Duration.zero);
    await controller.verifyAndMerge('123456');
    await controller.retry();
    expect(repository.mergeCalls, 1);
    repository.mergeGate!.complete(repository.conversion);
    await verify;

    expect(container.read(accountControllerProvider).uiState, AccountUiState.complete);
  });

  testWidgets('request error keeps identifier phase and localized retry', (
    tester,
  ) async {
    final repository = _ControllableAccountRepository()..requestFailures = 1;
    await _pumpScreen(
      tester,
      repository: repository,
      locale: const Locale('tr', 'TR'),
    );

    await tester.enterText(
      find.byKey(const ValueKey('account-identifier')),
      'person@example.com',
    );
    await tester.tap(find.byKey(const ValueKey('account-request-otp')));
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('account-identifier-surface')), findsOneWidget);
    expect(find.byKey(const ValueKey('account-code-surface')), findsNothing);
    expect(find.byKey(const ValueKey('account-error-surface')), findsOneWidget);
    expect(find.byKey(const ValueKey('account-error-retry')), findsOneWidget);
    expect(find.text('Kodu yeniden gönder'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('verification error keeps code phase', (tester) async {
    final repository = _ControllableAccountRepository()..verifyFailures = 1;
    await _pumpScreen(
      tester,
      repository: repository,
      locale: const Locale('en', 'US'),
    );

    await _advanceToCode(tester);
    await tester.enterText(
      find.byKey(const ValueKey('account-otp-code')),
      '123456',
    );
    await tester.tap(find.byKey(const ValueKey('account-verify-merge')));
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('account-code-surface')), findsOneWidget);
    expect(find.byKey(const ValueKey('account-identifier-surface')), findsNothing);
    expect(find.byKey(const ValueKey('account-error-surface')), findsOneWidget);
    expect(find.text('Edit code'), findsOneWidget);
    expect(repository.requestCalls, 1);
    expect(repository.verifyCalls, 1);
    expect(repository.mergeCalls, 0);
    expect(tester.takeException(), isNull);
  });

  testWidgets('merge error retry does not request or verify again', (
    tester,
  ) async {
    final repository = _ControllableAccountRepository()..mergeFailures = 1;
    await _pumpScreen(
      tester,
      repository: repository,
      locale: const Locale('en', 'US'),
    );

    await _advanceToCode(tester);
    await tester.enterText(
      find.byKey(const ValueKey('account-otp-code')),
      '123456',
    );
    await tester.tap(find.byKey(const ValueKey('account-verify-merge')));
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('account-code-surface')), findsNothing);
    expect(find.byKey(const ValueKey('account-error-surface')), findsOneWidget);
    expect(find.text('Retry history protection'), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('account-error-retry')));
    await tester.pumpAndSettle();

    expect(repository.requestCalls, 1);
    expect(repository.verifyCalls, 1);
    expect(repository.mergeCalls, 2);
    expect(find.byKey(const ValueKey('account-complete-surface')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  for (final themeMode in [ThemeMode.light, ThemeMode.dark]) {
    testWidgets(
      'account recovery is compact-safe in ${themeMode.name} theme',
      (tester) async {
        tester.view.physicalSize = const Size(360, 800);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);

        final repository = _ControllableAccountRepository()
          ..requestFailures = 1;
        await _pumpScreen(
          tester,
          repository: repository,
          locale: const Locale('tr', 'TR'),
          themeMode: themeMode,
          textScale: 1.6,
        );
        await tester.enterText(
          find.byKey(const ValueKey('account-identifier')),
          'person@example.com',
        );
        await tester.tap(find.byKey(const ValueKey('account-request-otp')));
        await tester.pumpAndSettle();

        expect(find.byKey(const ValueKey('account-error-surface')), findsOneWidget);
        expect(find.byKey(const ValueKey('account-error-retry')), findsOneWidget);
        expect(find.byKey(const ValueKey('account-continue-guest')), findsOneWidget);
        expect(tester.takeException(), isNull);
      },
    );
  }
}

ProviderContainer _container(AccountRepository repository) => ProviderContainer(
  overrides: [accountRepositoryProvider.overrideWithValue(repository)],
);

Future<void> _pumpScreen(
  WidgetTester tester, {
  required AccountRepository repository,
  required Locale locale,
  ThemeMode themeMode = ThemeMode.light,
  double textScale = 1,
}) async {
  tester.platformDispatcher.localeTestValue = locale;
  addTearDown(tester.platformDispatcher.clearLocaleTestValue);

  await tester.pumpWidget(
    ProviderScope(
      overrides: [accountRepositoryProvider.overrideWithValue(repository)],
      child: MaterialApp(
        debugShowCheckedModeBanner: false,
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
        themeMode: themeMode,
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(
            context,
          ).copyWith(textScaler: TextScaler.linear(textScale)),
          child: child!,
        ),
        home: const AccountConversionScreen(),
      ),
    ),
  );
  await tester.pump();
}

Future<void> _advanceToCode(WidgetTester tester) async {
  await tester.enterText(
    find.byKey(const ValueKey('account-identifier')),
    'person@example.com',
  );
  await tester.tap(find.byKey(const ValueKey('account-request-otp')));
  await tester.pumpAndSettle();
  expect(find.byKey(const ValueKey('account-code-surface')), findsOneWidget);
}

class _ControllableAccountRepository implements AccountRepository {
  final challenge = OtpChallenge(
    id: 'challenge-1',
    destinationHint: 'p***@example.com',
    expiresAt: DateTime.utc(2026, 8, 1, 14),
  );
  final verification = OtpVerification(
    token: 'verified-token',
    expiresAt: DateTime.utc(2026, 8, 1, 14),
  );
  final conversion = const AccountConversion(
    actorId: 'actor-1',
    mergedExistingHistory: true,
  );

  int requestFailures = 0;
  int verifyFailures = 0;
  int mergeFailures = 0;
  int requestCalls = 0;
  int verifyCalls = 0;
  int mergeCalls = 0;
  Completer<OtpChallenge>? requestGate;
  Completer<OtpVerification>? verifyGate;
  Completer<AccountConversion>? mergeGate;
  final List<String> mergeTokens = [];

  @override
  Future<OtpChallenge> requestOtp({
    required String channel,
    required String identifier,
  }) async {
    requestCalls += 1;
    final gate = requestGate;
    if (gate != null && !gate.isCompleted) return gate.future;
    if (requestFailures > 0) {
      requestFailures -= 1;
      throw const ClientTransportFailure(code: 'NETWORK_UNAVAILABLE');
    }
    return challenge;
  }

  @override
  Future<OtpVerification> verifyOtp({
    required String challengeId,
    required String code,
  }) async {
    verifyCalls += 1;
    final gate = verifyGate;
    if (gate != null && !gate.isCompleted) return gate.future;
    if (verifyFailures > 0) {
      verifyFailures -= 1;
      throw const ClientTransportFailure(code: 'NETWORK_UNAVAILABLE');
    }
    return verification;
  }

  @override
  Future<AccountConversion> mergeGuest({
    required String verificationToken,
  }) async {
    mergeCalls += 1;
    mergeTokens.add(verificationToken);
    final gate = mergeGate;
    if (gate != null && !gate.isCompleted) return gate.future;
    if (mergeFailures > 0) {
      mergeFailures -= 1;
      throw const ClientTransportFailure(code: 'NETWORK_UNAVAILABLE');
    }
    return conversion;
  }
}
