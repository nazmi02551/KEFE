import '../../../core/localization/kefe_locale_catalog.dart';
import '../../../core/localization/kefe_strings.dart';
import '../localization/account_recovery_string_catalog.dart';

extension AccountRecoveryStrings on KefeStrings {
  String _accountRecoveryText(
    String key, {
    Map<String, Object?> placeholders = const {},
  }) => KefeLocaleCatalog.resolve(
    locale: locale,
    resources: AccountRecoveryStringCatalog.resources,
    key: key,
    placeholders: placeholders,
  );

  String get accountRequesting => _accountRecoveryText('account.requesting');
  String get accountVerifying => _accountRecoveryText('account.verifying');
  String get accountMerging => _accountRecoveryText('account.merging');

  String accountRequestFailure(String code) => _accountRecoveryText(
    'account.request_failure',
    placeholders: {'code': code},
  );

  String accountVerifyFailure(String code) => _accountRecoveryText(
    'account.verify_failure',
    placeholders: {'code': code},
  );

  String accountMergeFailure(String code) => _accountRecoveryText(
    'account.merge_failure',
    placeholders: {'code': code},
  );

  String get accountRetryRequest =>
      _accountRecoveryText('account.retry_request');
  String get accountRetryCode => _accountRecoveryText('account.retry_code');
  String get accountRetryMerge => _accountRecoveryText('account.retry_merge');
}
