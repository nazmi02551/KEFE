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
  String get progressRetry =>
      _isTurkish ? 'İlerlemeyi tekrar yükle' : 'Retry progress';
  String get progressWeighs => _isTurkish ? 'Tartım' : 'Weighs';
  String get progressCases => _isTurkish ? 'Vaka' : 'Cases';
  String get progressDomains => _isTurkish ? 'Alan' : 'Domains';
  String get progressRecent =>
      _isTurkish ? 'Son tamamlananlar' : 'Recently completed';
  String get progressMethodology => _isTurkish
      ? 'Bu görünüm yalnızca kendi tamamlanmış tartımlarına dayanır; kişilik veya ideoloji çıkarımı yapılmaz.'
      : 'This view uses only your completed weighs. It does not infer personality or ideology.';

  String progressReadiness(String readiness) {
    return switch (readiness) {
      'FORMING' =>
        _isTurkish
            ? 'Karar geçmişin oluşmaya başladı.'
            : 'Your decision history is beginning to take shape.',
      _ =>
        _isTurkish
            ? 'Tartım yaptıkça karar geçmişin burada büyüyecek.'
            : 'Your decision history will grow here as you complete weighs.',
    };
  }

  String get journeyEyebrow => 'MY KEFE';
  String get journeyTitle =>
      _isTurkish ? 'Karar yolculuğun.' : 'Your decision journey.';
  String get journeySubtitle => _isTurkish
      ? 'Yalnızca KEFE’de kaydedilen tartım, yeniden tartım ve yansıma geçmişin.'
      : 'Only your recorded KEFE weigh, revisit and reflection history.';
  String get journeyPreviewNotice => _isTurkish
      ? 'Bu ekrandaki geçmiş Product Preview için hazırlanmış örnek veridir.'
      : 'History on this screen is example data prepared for Product Preview.';
  String get journeyRevisits => _isTurkish ? 'Yeniden tartım' : 'Revisits';
  String get journeyReflections => _isTurkish ? 'Yansıma' : 'Reflections';
  String get journeyDomainActivity =>
      _isTurkish ? 'Tartım alanların' : 'Your weigh activity';
  String get journeyRecent =>
      _isTurkish ? 'Son karar yolculukların' : 'Recent decision journeys';
  String get journeyRevisited => _isTurkish ? 'Yeniden tartıldı' : 'Revisited';
  String get journeyReflected =>
      _isTurkish ? 'Yansıma tamamlandı' : 'Reflection completed';
  String get journeyCommitted =>
      _isTurkish ? 'İlk karar kaydedildi' : 'Initial decision recorded';
  String get journeyEmpty => _isTurkish
      ? 'Henüz tamamlanmış bir tartım yok. İlk kararın burada görünmeye başlayacak.'
      : 'No completed weighs yet. Your first decision will begin your history here.';
  String get journeyNonInferenceNote => _isTurkish
      ? 'Bu özet yalnızca gözlenen uygulama geçmişini gösterir; kişilik, ideoloji, psikolojik profil veya neden-sonuç çıkarımı yapmaz.'
      : 'This summary only shows observed product history; it does not infer personality, ideology, psychological traits or causality.';
  String journeyWeighCount(int count) =>
      _isTurkish ? '$count tartım' : '$count weighs';
  String journeyUpdateCount(int count) => _isTurkish
      ? '$count yeniden tartım'
      : '$count ${count == 1 ? 'revisit' : 'revisits'}';

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
