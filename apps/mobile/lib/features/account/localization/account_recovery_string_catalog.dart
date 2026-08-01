import '../../../core/localization/kefe_locale_catalog.dart';

abstract final class AccountRecoveryStringCatalog {
  static const KefeLocaleResources resources = {
    'en': {
      'account.requesting': 'Sending the verification code…',
      'account.verifying': 'Verifying the code…',
      'account.merging': 'Protecting your existing history…',
      'account.request_failure':
          'We could not send a verification code · {code}',
      'account.verify_failure': 'We could not verify this code · {code}',
      'account.merge_failure':
          'Your code was verified, but history protection could not finish · {code}',
      'account.retry_request': 'Send code again',
      'account.retry_code': 'Edit code',
      'account.retry_merge': 'Retry history protection',
    },
    'tr': {
      'account.requesting': 'Doğrulama kodu gönderiliyor…',
      'account.verifying': 'Kod doğrulanıyor…',
      'account.merging': 'Mevcut geçmişin korunuyor…',
      'account.request_failure':
          'Doğrulama kodu gönderilemedi · {code}',
      'account.verify_failure': 'Bu kod doğrulanamadı · {code}',
      'account.merge_failure':
          'Kod doğrulandı ancak geçmiş koruması tamamlanamadı · {code}',
      'account.retry_request': 'Kodu yeniden gönder',
      'account.retry_code': 'Kodu düzenle',
      'account.retry_merge': 'Geçmiş korumasını yeniden dene',
    },
  };
}
