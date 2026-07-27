import 'package:flutter/widgets.dart';

class KefeStrings {
  const KefeStrings(this.locale);

  final Locale locale;

  static const supportedLocales = [Locale('tr', 'TR'), Locale('en', 'US')];

  static KefeStrings of(BuildContext context) {
    return Localizations.of<KefeStrings>(context, KefeStrings)!;
  }

  bool get _tr => locale.languageCode == 'tr';

  String get appName => 'KEFE';
  String get promise => _tr
      ? 'Kararını tart. Farklı düşünmenin nedenlerini gör.'
      : 'Weigh your decision. See why people differ.';
  String get onboardingTitleOne => _tr
      ? 'Önce kendi kararını gör.'
      : 'See your own decision first.';
  String get onboardingBodyOne => _tr
      ? 'KEFE sana çoğunluğun ne dediğini göstermeden önce, aynı konuya kendi gözünden bakmanı ister.'
      : 'Before showing what the crowd thinks, KEFE asks you to look at the same question through your own eyes.';
  String get onboardingStepTwoEyebrow => _tr ? 'Farkı keşfet' : 'Discover the difference';
  String get onboardingTitleTwo => _tr
      ? 'Sonra neden ayrıştığını keşfet.'
      : 'Then discover why views diverge.';
  String get onboardingBodyTwo => _tr
      ? 'Kararından sonra topluluk sonucunu, farklı perspektifleri ve zamanla fikrinin nasıl değiştiğini inceleyebilirsin.'
      : 'After your decision, you can inspect community results, different perspectives and how your view changes over time.';
  String get onboardingNext => _tr ? 'Devam et' : 'Continue';
  String get onboardingTryCase => _tr ? 'İlk tartımı yap' : 'Make your first weigh';
  String get continueAsGuest => _tr ? 'Misafir olarak devam et' : 'Continue as guest';
  String get firstRevealHelper => _tr
      ? 'İlk tartımın tamamlandı. KEFE’yi keşfetmeye misafir olarak devam edebilirsin.'
      : 'Your first weigh is complete. You can continue exploring KEFE as a guest.';
  String get exploreTitle => _tr ? 'Keşfet' : 'Explore';
  String get exploreIntro => _tr
      ? 'Önce sen karar ver. Sonra dünyayı gör.'
      : 'Decide first. Then see the world.';
  String get exploreEmpty => _tr
      ? 'Şu anda tartılacak bir içerik yok.'
      : 'There is nothing to weigh right now.';
  String get openCase => _tr ? 'Tartmaya Başla' : 'Start Weighing';
  String get loading => _tr ? 'Hazırlanıyor…' : 'Preparing…';
  String get retry => _tr ? 'Tekrar dene' : 'Try again';
  String get start => _tr ? 'Başla' : 'Start';
  String get commit => _tr ? 'Kararımı Ver' : 'Commit My Decision';
  String get retrySync => _tr ? 'Kararımı Senkronize Et' : 'Sync My Decision';
  String get commitHelper => _tr
      ? 'Kararını kilitle ve sonucu gör.'
      : 'Lock your decision and reveal the result.';
  String get completeRequired => _tr
      ? 'Devam etmek için zorunlu soruları yanıtla.'
      : 'Answer the required questions to continue.';
  String get requiredQuestion => _tr ? 'Zorunlu' : 'Required';
  String get optionalQuestion => _tr ? 'İsteğe bağlı' : 'Optional';
  String get unsupportedQuestionType => _tr
      ? 'Bu soru tipi bu sürümde desteklenmiyor.'
      : 'This question type is not supported in this version.';
  String get pendingHelper => _tr
      ? 'Kararın cihazda güvende. Aynı karar anahtarıyla güvenli biçimde yeniden denenecek.'
      : 'Your decision is safe on this device. It will retry with the same decision key.';
  String get offlineDraft => _tr
      ? 'Çevrimdışı taslak geri yüklendi.'
      : 'Offline draft restored.';
  String get revealPending => _tr
      ? 'Kararın kaydedildi. Sonuç bağlantı geldiğinde yeniden açılabilir.'
      : 'Your decision is committed. The result can be reopened when connectivity returns.';
  String get uncertainCommit => _tr
      ? 'Bağlantı kesildi. Kararın gönderilmiş olabilir; aynı anahtarla güvenli biçimde kontrol edeceğiz.'
      : 'Connection dropped. Your decision may already be committed; we will safely check with the same key.';
  String get revealTitle => _tr ? 'Topluluk nasıl tarttı?' : 'How did the community weigh it?';
  String get trustedSample => _tr ? 'Güvenilir örneklem' : 'Trusted sample';
  String get selectAnswer => _tr ? 'Bir seçenek seç' : 'Choose an option';
  String get genericError => _tr
      ? 'Bir sorun oluştu. Kararın kaybolmadı; tekrar deneyebilirsin.'
      : 'Something went wrong. Your decision was not lost; you can retry.';

  String messageForCode(String? code) {
    return switch (code) {
      'OFFLINE_DRAFT_RESTORED' => offlineDraft,
      'WEIGH_COMMIT_UNCERTAIN' => uncertainCommit,
      'RESULT_SYNC_PENDING' => revealPending,
      'NETWORK_UNAVAILABLE' || 'NETWORK_TIMEOUT' => _tr
          ? 'Bağlantı kurulamadı. Cihazdaki karar korunuyor.'
          : 'Could not connect. The decision on this device is preserved.',
      _ => genericError,
    };
  }
}

class KefeStringsDelegate extends LocalizationsDelegate<KefeStrings> {
  const KefeStringsDelegate();

  @override
  bool isSupported(Locale locale) => const {'tr', 'en'}.contains(locale.languageCode);

  @override
  Future<KefeStrings> load(Locale locale) async => KefeStrings(locale);

  @override
  bool shouldReload(KefeStringsDelegate old) => false;
}
