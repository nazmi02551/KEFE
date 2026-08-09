import 'kefe_locale_catalog.dart';

abstract final class PrivacyErrorStringCatalog {
  static const KefeLocaleResources resources = {
    'tr': {
      'auth_required':
          'Bu işlem için geçerli kullanıcı oturumu bulunamadı. Uygulamaya yeniden girip tekrar deneyin.',
      'identity_unavailable':
          'Gizlilik işlemi için gerekli kimlik bilgisi doğrulanamadı. Verileriniz silinmedi; lütfen tekrar deneyin.',
      'receipt_invalid':
          'Sunucudan güvenli silme onayı alınamadı. Verilerinizin silindiği varsayılmadı; lütfen tekrar deneyin.',
    },
    'en': {
      'auth_required':
          'No valid user session is available for this action. Re-enter the app and try again.',
      'identity_unavailable':
          'The identity required for this privacy action could not be verified. Your data was not treated as deleted; please try again.',
      'receipt_invalid':
          'A valid secure-deletion receipt was not received from the server. Your data was not treated as deleted; please try again.',
    },
  };
}
