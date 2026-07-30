import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../application/account_controller.dart';

class AccountConversionScreen extends ConsumerStatefulWidget {
  const AccountConversionScreen({super.key});

  @override
  ConsumerState<AccountConversionScreen> createState() =>
      _AccountConversionScreenState();
}

class _AccountConversionScreenState
    extends ConsumerState<AccountConversionScreen> {
  final _identifier = TextEditingController();
  final _code = TextEditingController();

  @override
  void dispose() {
    _identifier.dispose();
    _code.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final state = ref.watch(accountControllerProvider);
    final controller = ref.read(accountControllerProvider.notifier);

    return Scaffold(
      appBar: AppBar(title: Text(strings.accountTitle)),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Semantics(
              header: true,
              child: Text(
                strings.accountHeading,
                style: Theme.of(context).textTheme.headlineSmall,
              ),
            ),
            const SizedBox(height: 8),
            Text(strings.accountBody),
            const SizedBox(height: 20),
            if (state.uiState == AccountUiState.enterIdentifier ||
                state.uiState == AccountUiState.requesting ||
                state.uiState == AccountUiState.error) ...[
              SegmentedButton<String>(
                segments: [
                  ButtonSegment(
                    value: 'EMAIL',
                    label: Text(strings.accountEmail),
                  ),
                  ButtonSegment(
                    value: 'SMS',
                    label: Text(strings.accountPhone),
                  ),
                ],
                selected: {state.channel},
                onSelectionChanged: state.uiState == AccountUiState.requesting
                    ? null
                    : (value) => controller.setChannel(value.first),
              ),
              const SizedBox(height: 16),
              TextField(
                key: const ValueKey('account-identifier'),
                controller: _identifier,
                keyboardType: state.channel == 'EMAIL'
                    ? TextInputType.emailAddress
                    : TextInputType.phone,
                autofillHints: state.channel == 'EMAIL'
                    ? const [AutofillHints.email]
                    : const [AutofillHints.telephoneNumber],
                decoration: InputDecoration(
                  labelText: state.channel == 'EMAIL'
                      ? strings.accountEmailAddress
                      : strings.accountPhoneNumber,
                ),
                onChanged: controller.setIdentifier,
              ),
              const SizedBox(height: 16),
              FilledButton(
                key: const ValueKey('account-request-otp'),
                onPressed: state.uiState == AccountUiState.requesting
                    ? null
                    : controller.requestOtp,
                child: Text(strings.accountSendCode),
              ),
            ],
            if (state.uiState == AccountUiState.enterCode ||
                state.uiState == AccountUiState.verifying) ...[
              Text(
                strings.accountCodeInstruction(
                  state.challenge?.destinationHint ?? '',
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                key: const ValueKey('account-otp-code'),
                controller: _code,
                keyboardType: TextInputType.number,
                maxLength: 6,
                autofillHints: const [AutofillHints.oneTimeCode],
                decoration: InputDecoration(
                  labelText: strings.accountVerificationCode,
                ),
              ),
              FilledButton(
                key: const ValueKey('account-verify-merge'),
                onPressed: state.uiState == AccountUiState.verifying
                    ? null
                    : () => controller.verifyAndMerge(_code.text),
                child: Text(strings.accountConvert),
              ),
            ],
            if (state.uiState == AccountUiState.complete) ...[
              const Icon(Icons.verified_outlined, size: 44),
              const SizedBox(height: 12),
              Text(
                state.mergedExistingHistory
                    ? strings.accountMerged
                    : strings.accountPreserved,
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 16),
              FilledButton(
                onPressed: () => context.go('/my-kefe'),
                child: Text(strings.accountReturnMyKefe),
              ),
            ],
            if (state.errorCode != null) ...[
              const SizedBox(height: 16),
              Text(
                strings.accountFailure(state.errorCode!),
                key: const ValueKey('account-error'),
              ),
              const SizedBox(height: 8),
              OutlinedButton(
                onPressed: controller.retry,
                child: Text(strings.retry),
              ),
            ],
            const SizedBox(height: 16),
            TextButton(
              key: const ValueKey('account-continue-guest'),
              onPressed: () => context.pop(),
              child: Text(strings.continueAsGuest),
            ),
          ],
        ),
      ),
    );
  }
}
