import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/kefe_strings.dart';
import '../application/account_controller.dart';

class AccountConversionScreen extends ConsumerStatefulWidget {
  const AccountConversionScreen({super.key});

  @override
  ConsumerState<AccountConversionScreen> createState() => _AccountConversionScreenState();
}

class _AccountConversionScreenState extends ConsumerState<AccountConversionScreen> {
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
    final tr = Localizations.localeOf(context).languageCode == 'tr';
    final state = ref.watch(accountControllerProvider);
    final controller = ref.read(accountControllerProvider.notifier);

    return Scaffold(
      appBar: AppBar(
        title: Text(tr ? 'Hesabını koru' : 'Protect your history'),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Semantics(
              header: true,
              child: Text(
                tr ? 'Tartımların seninle gelsin.' : 'Keep your weighs with you.',
                style: Theme.of(context).textTheme.headlineSmall,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              tr
                  ? 'Hesap isteğe bağlıdır. Misafir olarak devam edebilirsin; hesap açarsan mevcut geçmişin sunucuda aynı kimliğe bağlanır.'
                  : 'An account is optional. You can stay a guest; converting preserves your existing server history under the same identity.',
            ),
            const SizedBox(height: 20),
            if (state.uiState == AccountUiState.enterIdentifier ||
                state.uiState == AccountUiState.requesting ||
                state.uiState == AccountUiState.error) ...[
              SegmentedButton<String>(
                segments: [
                  ButtonSegment(value: 'EMAIL', label: Text(tr ? 'E-posta' : 'Email')),
                  ButtonSegment(value: 'SMS', label: Text(tr ? 'Telefon' : 'Phone')),
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
                      ? (tr ? 'E-posta adresi' : 'Email address')
                      : (tr ? 'Telefon numarası' : 'Phone number'),
                ),
                onChanged: controller.setIdentifier,
              ),
              const SizedBox(height: 16),
              FilledButton(
                key: const ValueKey('account-request-otp'),
                onPressed: state.uiState == AccountUiState.requesting
                    ? null
                    : controller.requestOtp,
                child: Text(tr ? 'Doğrulama kodu gönder' : 'Send verification code'),
              ),
            ],
            if (state.uiState == AccountUiState.enterCode ||
                state.uiState == AccountUiState.verifying) ...[
              Text(
                tr
                    ? '${state.challenge?.destinationHint ?? ''} adresine gönderilen 6 haneli kodu gir.'
                    : 'Enter the 6-digit code sent to ${state.challenge?.destinationHint ?? ''}.',
              ),
              const SizedBox(height: 16),
              TextField(
                key: const ValueKey('account-otp-code'),
                controller: _code,
                keyboardType: TextInputType.number,
                maxLength: 6,
                autofillHints: const [AutofillHints.oneTimeCode],
                decoration: InputDecoration(labelText: tr ? 'Doğrulama kodu' : 'Verification code'),
              ),
              FilledButton(
                key: const ValueKey('account-verify-merge'),
                onPressed: state.uiState == AccountUiState.verifying
                    ? null
                    : () => controller.verifyAndMerge(_code.text),
                child: Text(tr ? 'Hesaba dönüştür' : 'Convert account'),
              ),
            ],
            if (state.uiState == AccountUiState.complete) ...[
              const Icon(Icons.verified_outlined, size: 44),
              const SizedBox(height: 12),
              Text(
                state.mergedExistingHistory
                    ? (tr ? 'Hesabın doğrulandı ve iki geçmiş güvenli biçimde birleştirildi.' : 'Account verified and both histories were safely merged.')
                    : (tr ? 'Hesabın doğrulandı. Mevcut tartım geçmişin korunuyor.' : 'Account verified. Your existing weigh history is preserved.'),
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 16),
              FilledButton(
                onPressed: () => context.go('/my-kefe'),
                child: Text(tr ? 'My KEFE’ye dön' : 'Return to My KEFE'),
              ),
            ],
            if (state.errorCode != null) ...[
              const SizedBox(height: 16),
              Text(
                '${tr ? 'İşlem tamamlanamadı' : 'Could not complete'} · ${state.errorCode}',
                key: const ValueKey('account-error'),
              ),
              const SizedBox(height: 8),
              OutlinedButton(
                onPressed: controller.retry,
                child: Text(KefeStrings.of(context).retry),
              ),
            ],
            const SizedBox(height: 16),
            TextButton(
              key: const ValueKey('account-continue-guest'),
              onPressed: () => context.pop(),
              child: Text(KefeStrings.of(context).continueAsGuest),
            ),
          ],
        ),
      ),
    );
  }
}
