import 'kefe_strings.dart';

extension InternalAlphaStrings on KefeStrings {
  bool get _iaTr => locale.languageCode == 'tr';

  String get primaryNavExplore => _iaTr ? 'Keşfet' : 'Explore';
  String get primaryNavWeigh => _iaTr ? 'Tartım' : 'Weigh';
  String get primaryNavActivity => _iaTr ? 'Aktivite' : 'Activity';
  String get primaryNavMyKefe => 'My KEFE';

  String get accountTitle => _iaTr ? 'Hesabını koru' : 'Protect your history';
  String get accountHeading =>
      _iaTr ? 'Tartımların seninle gelsin.' : 'Keep your weighs with you.';
  String get accountBody => _iaTr
      ? 'Hesap isteğe bağlıdır. Misafir olarak devam edebilirsin; hesap açarsan mevcut geçmişin sunucuda aynı kimliğe bağlanır.'
      : 'An account is optional. You can stay a guest; converting preserves your existing server history under the same identity.';
  String get accountEmail => _iaTr ? 'E-posta' : 'Email';
  String get accountPhone => _iaTr ? 'Telefon' : 'Phone';
  String get accountEmailAddress => _iaTr ? 'E-posta adresi' : 'Email address';
  String get accountPhoneNumber => _iaTr ? 'Telefon numarası' : 'Phone number';
  String get accountSendCode =>
      _iaTr ? 'Doğrulama kodu gönder' : 'Send verification code';
  String accountCodeInstruction(String destination) => _iaTr
      ? '$destination adresine gönderilen 6 haneli kodu gir.'
      : 'Enter the 6-digit code sent to $destination.';
  String get accountVerificationCode =>
      _iaTr ? 'Doğrulama kodu' : 'Verification code';
  String get accountConvert => _iaTr ? 'Hesaba dönüştür' : 'Convert account';
  String get accountMerged => _iaTr
      ? 'Hesabın doğrulandı ve iki geçmiş güvenli biçimde birleştirildi.'
      : 'Account verified and both histories were safely merged.';
  String get accountPreserved => _iaTr
      ? 'Hesabın doğrulandı. Mevcut tartım geçmişin korunuyor.'
      : 'Account verified. Your existing weigh history is preserved.';
  String get accountReturnMyKefe =>
      _iaTr ? 'My KEFE’ye dön' : 'Return to My KEFE';
  String get accountProtectAction =>
      _iaTr ? 'Geçmişimi koru' : 'Protect my history';
  String accountFailure(String code) =>
      '${_iaTr ? 'İşlem tamamlanamadı' : 'Could not complete'} · $code';

  String get activityEyebrow => _iaTr ? 'AKTİVİTE' : 'ACTIVITY';
  String get activityTitle =>
      _iaTr ? 'Kararlarına geri dön.' : 'Return to your decisions.';
  String get activitySubtitle => _iaTr
      ? 'Kaydettiğin vakalar, geçmiş kararların ve yeniden tartım izlerin burada birbirinden ayrı görünür.'
      : 'Saved Cases, past decisions and revisit history stay distinct here.';
  String get activityLoading =>
      _iaTr ? 'Aktiviten yükleniyor…' : 'Loading your activity…';
  String get activityUnavailable => _iaTr
      ? 'Aktivite şu anda yüklenemedi.'
      : 'Activity is currently unavailable.';
  String get activityRetry => _iaTr ? 'Tekrar dene' : 'Retry';
  String get activityEmpty => _iaTr
      ? 'Henüz geçmiş bir tartımın yok. İlk kararından sonra burada görünecek.'
      : 'You have no past weighs yet. They will appear after your first decision.';
  String get activityHistoryTitle =>
      _iaTr ? 'Karar geçmişin' : 'Decision history';
  String get activityCommitted =>
      _iaTr ? 'Karar verildi' : 'Decision committed';
  String get activityReflected =>
      _iaTr ? 'Yansıma tamamlandı' : 'Reflection completed';
  String activityUpdateCount(int count) => _iaTr
      ? '$count yeniden tartım'
      : '$count decision update${count == 1 ? '' : 's'}';
  String get activityPreviewNotice => _iaTr
      ? 'Bu ekrandaki karar geçmişi Product Preview örnek verisidir; canlı kullanıcı verisi değildir.'
      : 'Decision history on this screen is Product Preview sample data, not live user data.';

  String get weighHubEyebrow => _iaTr ? 'TARTIM' : 'WEIGH';
  String get weighHubTitle =>
      _iaTr ? 'Sıradaki kararını seç.' : 'Choose your next decision.';
  String get weighHubSubtitle => _iaTr
      ? 'Önce kendi kararını ver; topluluk sonucu yalnız Commit sonrasında açılır.'
      : 'Decide first; collective results unlock only after Commit.';
  String get weighHubRecommended =>
      _iaTr ? 'ÖNERİLEN TARTIM' : 'RECOMMENDED WEIGH';
  String get weighHubStart => _iaTr ? 'Tartıma başla' : 'Start weighing';
  String get weighHubMore => _iaTr ? 'Diğer tartımlar' : 'More Cases';
  String get weighHubEmpty => _iaTr
      ? 'Şu anda tartıma açık bir vaka yok.'
      : 'No Cases are currently open for weighing.';

  String get privacyTitle => _iaTr ? 'Gizlilik ve veriler' : 'Privacy and data';
  String get privacyHeading =>
      _iaTr ? 'Verilerin ve gizliliğin' : 'Your data and privacy';
  String get privacyBody => _iaTr
      ? 'Kendi ürün geçmişinin makine-okunur kopyasını alabilir veya hesabındaki/misafir kimliğindeki özel verileri silebilirsin.'
      : 'Export a machine-readable copy of your product history or delete private data attached to your account/guest identity.';
  String get privacyExportReady =>
      _iaTr ? 'Veri kopyan hazır' : 'Your data copy is ready';
  String get privacyExportCopied => _iaTr
      ? 'Makine-okunur JSON panoya kopyalandı. Güvenlik tokenları ve başka kullanıcıların verileri bu dışa aktarıma dahil değildir.'
      : 'Machine-readable JSON was copied to the clipboard. Security tokens and other users’ data are excluded.';
  String get privacyDone => _iaTr ? 'Tamam' : 'Done';
  String get privacyExport =>
      _iaTr ? 'Verilerimi dışa aktar' : 'Export my data';
  String get privacyDelete => _iaTr ? 'Verilerimi sil' : 'Delete my data';
  String privacyFailure(String code) =>
      '${_iaTr ? 'Gizlilik işlemi başarısız' : 'Privacy action failed'} · $code';
  String get privacyDeleteTitle =>
      _iaTr ? 'Verileri kalıcı olarak sil?' : 'Delete data permanently?';
  String get privacyDeleteBody => _iaTr
      ? 'Bu işlem geri alınamaz. Devam etmek için DELETE yaz.'
      : 'This cannot be undone. Type DELETE to continue.';
  String get privacyCancel => _iaTr ? 'Vazgeç' : 'Cancel';
  String get privacyDeletePermanently =>
      _iaTr ? 'Kalıcı olarak sil' : 'Delete permanently';

  String get shareTitle => _iaTr ? 'Bu vakayı paylaş' : 'Share this case';
  String get shareCaseOnlyNote => _iaTr
      ? 'MVP paylaşımı yalnız vakayı içerir. Kararın, güven puanın ve özel gerekçen bağlantıya eklenmez.'
      : 'MVP sharing is case-only. Your decision, confidence, and private reason are never included in the link.';
  String get sharePreparing =>
      _iaTr ? 'Bağlantı hazırlanıyor…' : 'Preparing link…';
  String get shareCreate =>
      _iaTr ? 'Vaka bağlantısı oluştur' : 'Create case link';
  String get shareCopied => _iaTr ? 'Bağlantı kopyalandı.' : 'Link copied.';
  String get shareCopy => _iaTr ? 'Kopyala' : 'Copy';
  String get shareRevoke => _iaTr ? 'Bağlantıyı iptal et' : 'Revoke link';
  String shareFailure(String code) =>
      '${_iaTr ? 'Paylaşım oluşturulamadı' : 'Share failed'} · $code';
  String get publicShareUnavailable => _iaTr
      ? 'Bu paylaşım artık kullanılamıyor.'
      : 'This share is no longer available.';
  String get publicShareRetry => _iaTr ? 'Tekrar dene' : 'Try again';
  String get publicShareEyebrow =>
      _iaTr ? 'Bir KEFE vakası paylaşıldı' : 'A KEFE case was shared';
  String get publicShareBlindFirst => _iaTr
      ? 'Paylaşan kişinin kararı burada gösterilmez. Önce aynı vakayı kendin tart ve kararını sabitle; topluluk sonucu ancak kendi Commit’inden sonra açılır.'
      : 'The sender’s decision is never shown here. Weigh the same case and Commit first; collective results unlock only after your own Commit.';
  String get publicShareWeigh => _iaTr ? 'Ben de tartayım' : 'Weigh it myself';

  String get communityTitle =>
      _iaTr ? 'Topluluk gerekçeleri' : 'Community reasons';
  String get communityPrivateNote => _iaTr
      ? 'Özel gerekçen burada otomatik yayınlanmaz. Topluluğa katkı ayrı bir eylemdir; metinli katkılar moderasyondan geçer.'
      : 'Your private reason is never published here automatically. Community contribution is a separate action; text contributions are moderated.';
  String get communityPublishHeading =>
      _iaTr ? 'Sen de ayrı bir gerekçe yayınla' : 'Publish a separate reason';
  String get communityOptionalText =>
      _iaTr ? 'İsteğe bağlı kısa metin' : 'Optional short text';
  String get communityModerationNote => _iaTr
      ? 'Metin varsa yayınlanmadan önce moderasyon bekler.'
      : 'Text waits for moderation before public display.';
  String get communitySubmitting => _iaTr ? 'Gönderiliyor…' : 'Submitting…';
  String get communityPublish =>
      _iaTr ? 'Topluluğa yayınla' : 'Publish to community';
  String get communityReceiptPending => _iaTr
      ? 'Katkın alındı. Metin moderasyon sonrası görünür olabilir.'
      : 'Contribution received. Text may become visible after moderation.';
  String get communityReceiptAllowed => _iaTr
      ? 'Katkın topluluk gerekçelerine eklendi.'
      : 'Your contribution was added to Community Reasons.';
  String communityUnavailable(String code) =>
      '${_iaTr ? 'Topluluk verisi kullanılamıyor' : 'Community data unavailable'} · $code';
  String get communityPublished =>
      _iaTr ? 'Yayınlanan gerekçeler' : 'Published reasons';
  String get communityResonates => _iaTr ? 'Bende yankılandı' : 'Resonates';
  String get communityUseful => _iaTr ? 'Faydalı' : 'Useful';
  String get communityReport => _iaTr ? 'Raporla' : 'Report';

  String get consensusLoading =>
      _iaTr ? 'Konsensüs kartı hazırlanıyor…' : 'Preparing consensus card…';
  String get consensusCommitFirst =>
      _iaTr ? 'Önce kararını sabitle' : 'Commit your decision first';
  String get consensusCommitFirstBody => _iaTr
      ? 'Konsensüs katılımı yalnız tamamlanmış bir tartımdan sonra açılır.'
      : 'Consensus participation unlocks only after a completed weigh.';
  String get consensusRetry => _iaTr ? 'Tekrar dene' : 'Retry';
  String get consensusExposed => _iaTr
      ? 'EXPOSED · Ana sonuç örneklemine dahil değil'
      : 'EXPOSED · Not part of the core result sample';
  String get consensusPrompt => _iaTr
      ? 'Bu ifadeye ne kadar katılıyorsun? Kartın dağılımı kendi yanıtından sonra açılır.'
      : 'How much do you agree? This card’s distribution unlocks after your own response.';
  String consensusReasonLimit(int max) => _iaTr
      ? 'Gerekçeni en fazla $max etiketle belirt'
      : 'Choose up to $max reason tags';
  String get consensusSubmitting =>
      _iaTr ? 'Katılım kaydediliyor…' : 'Submitting…';
  String get consensusJoin => _iaTr ? 'Sen de Katıl' : 'Join the consensus';
  String get consensusExposedMethodology => _iaTr
      ? 'Bu katılım, kararını verdikten sonra gerçekleştiği için EXPOSED olarak tutulur. Ana sonuç veya Signal değildir.'
      : 'Because this happens after your decision, it is stored as EXPOSED. It is not the core result or a Signal.';
  String get consensusDistribution =>
      _iaTr ? 'KONSENSÜS DAĞILIMI' : 'CONSENSUS DISTRIBUTION';
  String get consensusReasonPatterns =>
      _iaTr ? 'GEREKÇE ÖRÜNTÜLERİ' : 'REASON PATTERNS';
  String get consensusEyebrow =>
      _iaTr ? 'WE · ORTAK ZEMİN' : 'WE · COMMON GROUND';
  String get consensusCardTitle => _iaTr ? 'Konsensüs Kartı' : 'Consensus Card';
  String consensusUnavailable(String? code) =>
      '${_iaTr ? 'Konsensüs geçici olarak kullanılamıyor' : 'Consensus temporarily unavailable'}${code == null ? '' : ' · $code'}';
  String consensusStanceLabel(String code) => switch (code) {
    'AGREE' => _iaTr ? 'Katılıyorum' : 'Agree',
    'MIXED' => _iaTr ? 'Kısmen' : 'Mixed',
    'DISAGREE' => _iaTr ? 'Katılmıyorum' : 'Disagree',
    _ => code.replaceAll('_', ' '),
  };
  String consensusReasonLabel(String code) => switch (code) {
    'FAIRNESS' => _iaTr ? 'Adalet' : 'Fairness',
    'NEED' => _iaTr ? 'İhtiyaç' : 'Need',
    'RULES' => _iaTr ? 'Kurallar' : 'Rules',
    'PRACTICAL_IMPACT' => _iaTr ? 'Pratik etki' : 'Practical impact',
    'RESPONSIBILITY' => _iaTr ? 'Sorumluluk' : 'Responsibility',
    _ => code.replaceAll('_', ' '),
  };

  String domainName(String code) => switch (code) {
    'DAILY_LIFE' => _iaTr ? 'Günlük yaşam' : 'Daily life',
    'TECHNOLOGY' || 'TECHNOLOGY_AI' => _iaTr ? 'Teknoloji' : 'Technology',
    'SPORTS' => _iaTr ? 'Spor' : 'Sports',
    'CIVIC' || 'CITY_PUBLIC_LIFE' => _iaTr ? 'Kamusal' : 'Civic',
    'WORK_ECONOMY' ||
    'WORK_BUSINESS' => _iaTr ? 'İş & Ekonomi' : 'Work & Economy',
    'EDUCATION' => _iaTr ? 'Eğitim' : 'Education',
    'FAMILY_PARENTING' => _iaTr ? 'Aile & Ebeveynlik' : 'Family & Parenting',
    'CULTURE_MEDIA' => _iaTr ? 'Kültür & Medya' : 'Culture & Media',
    _ => code.replaceAll('_', ' '),
  };

  String get contextEventSummary => _iaTr ? 'Olay özeti' : 'Event summary';
  String get contextInformationStatus =>
      _iaTr ? 'Bilgi durumu' : 'Information status';
  String get journeyLabel => _iaTr ? 'KARAR YOLCULUĞU' : 'DECISION JOURNEY';
  String get stepCase => _iaTr ? 'Olay' : 'Case';
  String get stepWeigh => _iaTr ? 'Tartım' : 'Weigh';
  String get stepResult => _iaTr ? 'Sonuç' : 'Result';
  String get stepReflection => _iaTr ? 'Yansıma' : 'Reflection';
  String get stepCompleted => _iaTr ? 'Tamamlandı' : 'Completed';
  String get resultEyebrow => _iaTr ? 'SONUÇLAR' : 'RESULTS';
  String get yourDecision => _iaTr ? 'SENİN KARARIN' : 'YOUR DECISION';
  String get communityDistribution =>
      _iaTr ? 'TOPLULUK DAĞILIMI' : 'COMMUNITY DISTRIBUTION';
  String get kefeGap => _iaTr ? 'KEFE UÇURUMU' : 'KEFE GAP';
  String gapInsight({required bool selectedIsTop, required int percent}) =>
      selectedIsTop
      ? (_iaTr
            ? 'Seçimin toplulukta en yüksek paya sahip. Katılımcıların %$percent kadarı aynı seçeneği tercih etti.'
            : 'Your choice has the largest share in the community. $percent% of participants chose the same option.')
      : (_iaTr
            ? 'Seçtiğin seçenek toplulukta çoğunluk değil. Katılımcıların %$percent kadarı aynı seçeneği tercih etti.'
            : 'Your choice is not the community majority. $percent% of participants chose the same option.');
  String gapDifferenceInsight({
    required int selectedPercent,
    required int gapPoints,
  }) => _iaTr
      ? 'Seçtiğin seçenek toplulukta %$selectedPercent. En yüksek paya sahip seçenekle fark $gapPoints yüzde puan.'
      : 'Your choice has $selectedPercent% of the community. The gap to the leading option is $gapPoints percentage points.';
  String get decisionYou => _iaTr ? 'Sen' : 'You';
  String get balanceNoSelection =>
      _iaTr ? 'Henüz seçim yok' : 'No selection yet';
  String balanceSemantics(String selectedLabel) =>
      _iaTr ? 'KEFE terazisi. $selectedLabel' : 'KEFE balance. $selectedLabel';
  String resultMethodology({
    required int sampleSize,
    required String confidence,
  }) => '$trustedSample · n=$sampleSize · ${confidenceLabel(confidence)}';
  String confidenceLabel(String code) => switch (code) {
    'HIGH' => _iaTr ? 'Yüksek güven' : 'High confidence',
    'MEDIUM' => _iaTr ? 'Orta güven' : 'Medium confidence',
    'LOW' => _iaTr ? 'Düşük güven' : 'Low confidence',
    _ => code.replaceAll('_', ' '),
  };
  String get perspectiveEyebrow => _iaTr ? 'KARŞI GÖRÜŞLER' : 'COUNTER VIEWS';
  String get questionConfidence => _iaTr ? 'EMİNLİK' : 'CONFIDENCE';
  String get questionDecision => _iaTr ? 'KARAR' : 'DECISION';
  String get reasonsEyebrow => _iaTr ? 'GEREKÇELER' : 'REASONS';
}
