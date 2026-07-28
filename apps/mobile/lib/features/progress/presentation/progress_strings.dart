import '../../../core/localization/kefe_strings.dart';

extension ProgressStrings on KefeStrings {
  bool get _isTurkish => locale.languageCode == 'tr';

  String get progressTitle => _isTurkish ? 'Benim Kefem' : 'My KEFE';
  String get progressLoading => _isTurkish
      ? 'Tartım geçmişin hazırlanıyor…'
      : 'Preparing your weigh history…';
  String get progressUnavailable => _isTurkish
      ? 'Sonucun hazır. Kişisel ilerleme şu anda yüklenemedi.'
      : 'Your result is ready. Personal progress could not load right now.';
  String get progressRetry => _isTurkish ? 'İlerlemeyi tekrar yükle' : 'Retry progress';
  String get progressWeighs => _isTurkish ? 'Tartım' : 'Weighs';
  String get progressCases => _isTurkish ? 'Vaka' : 'Cases';
  String get progressDomains => _isTurkish ? 'Alan' : 'Domains';
  String get progressRecent => _isTurkish ? 'Son tamamlananlar' : 'Recently completed';
  String get progressMethodology => _isTurkish
      ? 'Bu görünüm yalnızca kendi tamamlanmış tartımlarına dayanır. Henüz kişilik veya ideoloji çıkarımı yapılmaz.'
      : 'This view uses only your completed weighs. It does not infer personality or ideology.';

  String progressReadiness(String readiness) {
    return switch (readiness) {
      'FORMING' => _isTurkish
          ? 'Karar örüntün oluşmaya başladı.'
          : 'Your decision pattern is beginning to form.',
      _ => _isTurkish
          ? 'Daha fazla tartımla kişisel içgörüler oluşmaya başlayacak.'
          : 'More weighs are needed before personal insights begin to form.',
    };
  }

  String get accountOfferTitle => _isTurkish
      ? 'İlerlemeni gelecekte de koru'
      : 'Protect your progress for the future';
  String get accountOfferBody => _isTurkish
      ? 'KEFE hesabı, ilerlemeni cihaz değişikliklerinde korumak için kullanılabilecek. Misafir olarak devam etmek her zaman mümkün.'
      : 'A KEFE account can later protect your progress across device changes. Continuing as a guest always remains available.';
  String get accountOfferUnavailable => _isTurkish
      ? 'Hesap oluşturma henüz açılmadı; çalışmayan bir kayıt adımı göstermiyoruz.'
      : 'Account creation is not available yet, so no non-functional sign-up action is shown.';
}
