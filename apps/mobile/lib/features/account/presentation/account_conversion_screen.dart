import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
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
  bool _otpComplete = false;

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
    final visual = context.kefeVisual;

    final showIdentifier =
        state.uiState == AccountUiState.enterIdentifier ||
        state.uiState == AccountUiState.requesting ||
        state.uiState == AccountUiState.error;
    final showCode =
        state.uiState == AccountUiState.enterCode ||
        state.uiState == AccountUiState.verifying;

    return Scaffold(
      appBar: AppBar(
        backgroundColor: visual.surfaceRaised,
        foregroundColor: visual.foreground,
        title: Text(strings.accountTitle),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Divider(height: 1, thickness: 1, color: visual.border),
        ),
      ),
      body: SafeArea(
        child: ListView(
          key: const ValueKey('account-conversion-screen'),
          padding: const EdgeInsets.fromLTRB(18, 18, 18, 32),
          children: [
            KefeSurface(
              key: const ValueKey('account-intro-surface'),
              tone: KefeSurfaceTone.raised,
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _AccountIcon(
                    icon: Icons.person_add_alt_1_rounded,
                    color: visual.goldSoft,
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Semantics(
                          header: true,
                          child: Text(
                            strings.accountHeading,
                            style: Theme.of(context).textTheme.headlineSmall
                                ?.copyWith(fontWeight: FontWeight.w900),
                          ),
                        ),
                        const SizedBox(height: 7),
                        Text(
                          strings.accountBody,
                          style: Theme.of(context).textTheme.bodyMedium
                              ?.copyWith(
                                color: visual.mutedForeground,
                                height: 1.45,
                              ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            if (showIdentifier) ...[
              const SizedBox(height: 16),
              KefeSurface(
                key: const ValueKey('account-identifier-surface'),
                tone: KefeSurfaceTone.raised,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    SegmentedButton<String>(
                      segments: [
                        ButtonSegment(
                          value: 'EMAIL',
                          icon: const Icon(Icons.mail_outline_rounded),
                          label: Text(strings.accountEmail),
                        ),
                        ButtonSegment(
                          value: 'SMS',
                          icon: const Icon(Icons.sms_outlined),
                          label: Text(strings.accountPhone),
                        ),
                      ],
                      selected: {state.channel},
                      onSelectionChanged:
                          state.uiState == AccountUiState.requesting
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
                        prefixIcon: Icon(
                          state.channel == 'EMAIL'
                              ? Icons.alternate_email_rounded
                              : Icons.phone_outlined,
                        ),
                      ),
                      onChanged: controller.setIdentifier,
                    ),
                    const SizedBox(height: 16),
                    FilledButton.icon(
                      key: const ValueKey('account-request-otp'),
                      onPressed:
                          state.uiState == AccountUiState.requesting ||
                              state.identifier.trim().isEmpty
                          ? null
                          : () => _requestOtp(controller),
                      icon: state.uiState == AccountUiState.requesting
                          ? const Icon(Icons.hourglass_top_rounded)
                          : const Icon(Icons.arrow_forward_rounded),
                      label: Text(strings.accountSendCode),
                    ),
                  ],
                ),
              ),
            ],
            if (showCode) ...[
              const SizedBox(height: 16),
              KefeSurface(
                key: const ValueKey('account-code-surface'),
                tone: KefeSurfaceTone.raised,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _AccountIcon(
                          icon: Icons.password_rounded,
                          color: visual.goldSoft,
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            strings.accountCodeInstruction(
                              state.challenge?.destinationHint ?? '',
                            ),
                            style: Theme.of(context).textTheme.bodyLarge
                                ?.copyWith(
                                  height: 1.4,
                                  fontWeight: FontWeight.w600,
                                ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      key: const ValueKey('account-otp-code'),
                      controller: _code,
                      enabled: state.uiState != AccountUiState.verifying,
                      keyboardType: TextInputType.number,
                      inputFormatters: [
                        FilteringTextInputFormatter.digitsOnly,
                      ],
                      maxLength: 6,
                      autofillHints: const [AutofillHints.oneTimeCode],
                      decoration: InputDecoration(
                        labelText: strings.accountVerificationCode,
                        prefixIcon: const Icon(Icons.pin_outlined),
                      ),
                      onChanged: (value) {
                        final complete = value.length == 6;
                        if (_otpComplete != complete) {
                          setState(() => _otpComplete = complete);
                        }
                        controller.clearError();
                      },
                    ),
                    FilledButton.icon(
                      key: const ValueKey('account-verify-merge'),
                      onPressed:
                          state.uiState == AccountUiState.verifying ||
                              !_otpComplete
                          ? null
                          : () => controller.verifyAndMerge(_code.text),
                      icon: state.uiState == AccountUiState.verifying
                          ? const Icon(Icons.hourglass_top_rounded)
                          : const Icon(Icons.verified_user_outlined),
                      label: Text(strings.accountConvert),
                    ),
                  ],
                ),
              ),
            ],
            if (state.uiState == AccountUiState.complete) ...[
              const SizedBox(height: 16),
              KefeSurface(
                key: const ValueKey('account-complete-surface'),
                tone: KefeSurfaceTone.premium,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Icon(Icons.verified_outlined, size: 46),
                    const SizedBox(height: 14),
                    Text(
                      state.mergedExistingHistory
                          ? strings.accountMerged
                          : strings.accountPreserved,
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w900,
                        color: visual.onSurfaceStrong,
                      ),
                    ),
                    const SizedBox(height: 18),
                    FilledButton(
                      onPressed: () => context.go('/my-kefe'),
                      child: Text(strings.accountReturnMyKefe),
                    ),
                  ],
                ),
              ),
            ],
            if (state.errorCode != null) ...[
              const SizedBox(height: 16),
              KefeSurface(
                key: const ValueKey('account-error-surface'),
                tone: KefeSurfaceTone.sunken,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(
                          Icons.error_outline_rounded,
                          color: Theme.of(context).colorScheme.error,
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            strings.accountFailure(state.errorCode!),
                            key: const ValueKey('account-error'),
                            style: TextStyle(
                              color: Theme.of(context).colorScheme.error,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    OutlinedButton(
                      key: const ValueKey('account-error-retry'),
                      onPressed: controller.retry,
                      child: Text(strings.retry),
                    ),
                  ],
                ),
              ),
            ],
            const SizedBox(height: 14),
            TextButton.icon(
              key: const ValueKey('account-continue-guest'),
              onPressed: () => context.pop(),
              icon: const Icon(Icons.arrow_back_rounded),
              label: Text(strings.continueAsGuest),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _requestOtp(AccountController controller) async {
    _code.clear();
    if (_otpComplete) setState(() => _otpComplete = false);
    await controller.requestOtp();
  }
}

class _AccountIcon extends StatelessWidget {
  const _AccountIcon({required this.icon, required this.color});

  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: visual.border),
      ),
      child: SizedBox.square(
        dimension: 42,
        child: Icon(icon, size: 21, color: color),
      ),
    );
  }
}
