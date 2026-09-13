import 'kefe_locale_catalog.dart';

abstract final class CoreStringCatalog {
  static const KefeLocaleResources resources = {
    'en': {
      'promise': 'Weigh your decision. See why people differ.',
      'onboarding.title_one': 'See your own decision first.',
      'onboarding.body_one':
          'Before showing what the crowd thinks, KEFE asks you to look at the same question through your own eyes.',
      'onboarding.step_two_eyebrow': 'Discover the difference',
      'onboarding.title_two': 'Then discover why views diverge.',
      'onboarding.body_two':
          'After your decision, you can inspect community results, different perspectives and how your view changes over time.',
      'onboarding.next': 'Continue',
      'onboarding.try_case': 'Make your first weigh',
      'onboarding.continue_as_guest': 'Continue as guest',
      'onboarding.first_reveal_helper':
          'Your first weigh is complete. You can continue exploring KEFE as a guest.',
      'explore.title': 'Explore',
      'explore.intro': 'Decide first. Then see the world.',
      'explore.empty': 'There is nothing to weigh right now.',
      'explore.open_case': 'Start Weighing',
      'context.title': 'Context',
      'context.helper':
          'Before deciding, review verified information separately from claims and uncertainty.',
      'context.details': 'Show details',
      'context.sources': 'View sources',
      'context.loading': 'Preparing context…',
      'context.unavailable':
          'Context could not load right now. No result or community information was shown.',
      'context.retry': 'Retry context',
      'context.claim.verified': 'Verified',
      'context.claim.claimed': 'Claimed',
      'context.claim.disputed': 'Disputed',
      'context.claim.unknown': 'Unknown',
      'context.information_status_guide.title': 'What do these information states mean?',
      'context.information_status_guide.helper':
          'A state belongs to the information block; it does not independently verify a linked source.',
      'context.information_status_guide.verified_desc':
          'The editorial record marks this block as checked.',
      'context.information_status_guide.claimed_desc':
          'This block presents a claim and is not marked verified.',
      'context.information_status_guide.disputed_desc':
          'The available record contains disagreement about this block.',
      'context.information_status_guide.unknown_desc':
          'The current record does not establish a status for this block.',
      'context.source.official': 'Official source',
      'context.source.news': 'News source',
      'context.source.research': 'Research',
      'context.source.editorial': 'Editorial source',
      'context.source.other': 'Other source',
      'common.loading': 'Preparing…',
      'common.retry': 'Try again',
      'common.start': 'Start',
      'decision.commit': 'Commit My Decision',
      'decision.retry_sync': 'Sync My Decision',
      'decision.commit_helper': 'Lock your decision and reveal the result.',
      'decision.complete_required':
          'Answer the required questions to continue.',
      'decision.required_question': 'Required',
      'decision.optional_question': 'Optional',
      'decision.unsupported_question_type':
          'This question type is not supported in this version.',
      'reason.title': 'Why did you think this?',
      'reason.helper':
          'Optionally choose what shaped your decision. In this version it is not shown to other users; short text may be reviewed for safety.',
      'reason.selection_limit': 'You can choose up to {maxTags} reasons.',
      'reason.text_label': 'Short reason',
      'reason.text_hint': 'Optionally add it in your own words…',
      'reason.tag.fairness': 'Fairness',
      'reason.tag.need': 'Need',
      'reason.tag.responsibility': 'Responsibility',
      'reason.tag.empathy': 'Empathy',
      'reason.tag.rules': 'Rules',
      'reason.tag.consequence': 'Consequence',
      'reason.tag.proportionality': 'Proportionality',
      'reason.tag.practical_impact': 'Practical impact',
      'sync.pending_helper':
          'Your decision is safe on this device. It will retry with the same decision key.',
      'sync.offline_draft': 'Offline draft restored.',
      'sync.decision_pending':
          'Your answers and reason are safe on this device. Pre-commit sync will retry when connectivity returns.',
      'sync.reveal_pending':
          'Your decision is committed. The result can be reopened when connectivity returns.',
      'sync.uncertain_commit':
          'Connection dropped. Your decision may already be committed; we will safely check with the same key.',
      'reveal.title': 'How did the community weigh it?',
      'reveal.trusted_sample': 'Trusted sample',
      'reveal.select_answer': 'Choose an option',
      'reflection.title': 'Look at your decision again',
      'reflection.decision_changed':
          '{count} response changed between your two decisions.',
      'reflection.decision_unchanged':
          'No response change is visible between your two decisions.',
      'reflection.intervention_summary':
          '{count} recorded encounter sits between the two decisions.',
      'reflection.non_causal_note':
          'This view shows the change and intervening encounters together; it does not claim that an encounter caused the change.',
      'reflection.complete': 'Complete reflection',
      'reflection.completed': 'Reflection completed',
      'reflection.loading': 'Preparing reflection…',
      'reflection.retry': 'Retry reflection',
      'flow.capability_pending.title': 'This step is not available yet',
      'flow.capability_pending.decision_revision':
          'This flow includes a re-weigh step. It will unlock here when decision revision support is available.',
      'flow.capability_pending.reflection_runtime':
          'This flow’s reflection step is being prepared. Your current decision has not been changed.',
      'flow.capability_pending.default':
          'The flow recognizes this step, but this version does not execute it yet. Other supported steps remain available.',
      'flow.offline_unavailable':
          'This older offline draft has no verified flow snapshot. The flow will be fetched from the server when connectivity returns; the app will not invent a default screen order.',
      'flow.runtime_unavailable':
          'The verified decision flow is currently unavailable for this case.',
      'flow.runtime_mismatch':
          'The decision flow did not match this session’s case version. Reload safely.',
      'perspective.title': 'See other perspectives',
      'perspective.loading': 'Preparing perspectives…',
      'perspective.retry': 'Retry perspectives',
      'perspective.unavailable':
          'Your result is ready. Perspectives could not load right now; you can retry without resending your decision.',
      'perspective.curated_note':
          'For now, verified curated perspectives are shown.',
      'perspective.cluster_pending':
          'You can view the available perspectives while broader processing continues.',
      'perspective.empty':
          'There is no eligible counter-perspective for this case right now.',
      'perspective.reason_pending_moderation':
          'Your short reason is under safety review. This does not mean it is a source for the perspectives below.',
      'perspective.methodology': 'About this view',
      'perspective.slot.near': 'Nearby perspective',
      'perspective.slot.opposing': 'Opposing perspective',
      'perspective.slot.bridge': 'Bridge perspective',
      'perspective.slot.alternative_context': 'Alternative context',
      'perspective.source.curated': 'Editorially curated',
      'perspective.source.human_reason': 'Human reason',
      'perspective.source.default': 'Source information',
      'error.generic':
          'Something went wrong. Your decision was not lost; you can retry.',
      'error.network_unavailable':
          'Could not connect. The decision on this device is preserved.',
      'error.guest_continuity_required':
          'This guest session can no longer be renewed. KEFE did not silently replace it with a new identity.',
      'error.account_reauthentication_required':
          'This account session ended. Verify your account again to restore access to its history.',
      'error.legacy_continuity_required':
          'This earlier session could not be upgraded safely. KEFE did not create a replacement guest identity.',
      'signal.card_eyebrow': 'COMMUNITY SIGNAL',
      'signal.tier_gold': 'Gold Consensus (High Confidence)',
      'signal.tier_silver': 'Silver Consensus (Verified Sample)',
      'signal.tier_bronze': 'Bronze Consensus (Developing Signal)',
      'signal.agreement_badge': '%{pct} Consensus (n={count})',
      'signal.provisional_label': 'PENDING EDITORIAL REVIEW',
      'institution.eyebrow': 'VERIFIED INSTITUTION RESPONSE',
      'institution.verified_badge': 'Official & Verified',
      'institution.milestone_label': 'Target milestone: {date}',
      'institution.type_acknowledge': 'Formal Acknowledgment',
      'institution.type_commitment': 'Binding Commitment',
      'institution.type_policy_change': 'Policy / Regulatory Change',
      'institution.type_clarification': 'Factual Clarification',
      'institution.type_decline': 'Declined with Stated Reason',
      'retry_action': 'Try Again',
      // Signal screen
      'signal_screen.title': 'Signals',
      'signal_screen.subtitle': 'Collective decisions that have passed qualification thresholds.',
      'signal_screen.methodology_note': 'Collective Result is not automatically Signal or truth. Each card has passed scale, integrity and methodology gates.',
      'signal_screen.load_error': 'Could not load signals. Please try again.',
      'signal_screen.empty': 'No qualified signals yet. Signals appear when collective results meet thresholds.',
      'signal_screen.provisional_label': 'EDITORIAL REVIEW PENDING',

      // Impact screen
      'impact.title': 'Impact',
      'impact.subtitle': 'Qualified signals that have reached institutions and triggered action.',
      'impact.institution_responses_title': 'Institution Responses',
      'impact.actions_title': 'Action Milestones',
      'impact.load_error': 'Could not load impact data. Please try again.',
      'impact.no_responses': 'No institution responses yet. Qualified signals will appear here.',
      'impact.no_actions': 'No action milestones recorded yet.',
      'impact.methodology_note': 'Collective Result is not automatically Signal, truth or authority. Signals reaching this screen have passed scale, integrity and methodology thresholds.',
      // About screen
      'about.title': 'About KEFE',
      'about.methodology_title': 'Methodology',
      'about.commit_first': 'Commit First',
      'about.commit_first_desc': 'You decide before seeing what others think. This blocks social pressure and herd effects.',
      'about.blind_first': 'Blind First',
      'about.blind_first_desc': 'Results and perspectives are only visible after your commitment. Pre-result isolation is both a product feature and a privacy guarantee.',
      'about.signal_title': 'Signal → Impact',
      'about.signal_desc': 'Not every collective result is a Signal. Signals must pass scale, integrity and methodology thresholds before reaching institutions.',
      'about.version_label': 'v2.0 · 2026-09-13',
    },
    'tr': {
      'promise': 'Kararını tart. Farklı düşünmenin nedenlerini gör.',
      'onboarding.title_one': 'Önce kendi kararını gör.',
      'onboarding.body_one':
          'KEFE sana çoğunluğun ne dediğini göstermeden önce, aynı konuya kendi gözünden bakmanı ister.',
      'onboarding.step_two_eyebrow': 'Farkı keşfet',
      'onboarding.title_two': 'Sonra neden ayrıştığını keşfet.',
      'onboarding.body_two':
          'Kararından sonra topluluk sonucunu, farklı perspektifleri ve zamanla fikrinin nasıl değiştiğini inceleyebilirsin.',
      'onboarding.next': 'Devam et',
      'onboarding.try_case': 'İlk tartımı yap',
      'onboarding.continue_as_guest': 'Misafir olarak devam et',
      'onboarding.first_reveal_helper':
          'İlk tartımın tamamlandı. KEFE’yi keşfetmeye misafir olarak devam edebilirsin.',
      'explore.title': 'Keşfet',
      'explore.intro': 'Önce sen karar ver. Sonra dünyayı gör.',
      'explore.empty': 'Şu anda tartılacak bir içerik yok.',
      'explore.open_case': 'Tartmaya Başla',
      'context.title': 'Bağlam',
      'context.helper':
          'Karar vermeden önce doğrulanmış bilgiler ile iddia ve belirsizlikleri ayrı ayrı incele.',
      'context.details': 'Ayrıntıları aç',
      'context.sources': 'Kaynakları gör',
      'context.loading': 'Bağlam hazırlanıyor…',
      'context.unavailable':
          'Bağlam şu anda yüklenemedi. Sonuç veya topluluk bilgisi gösterilmedi.',
      'context.retry': 'Bağlamı tekrar yükle',
      'context.claim.verified': 'Doğrulandı',
      'context.claim.claimed': 'İddia',
      'context.claim.disputed': 'Çelişkili',
      'context.claim.unknown': 'Bilinmiyor',
      'context.information_status_guide.title': 'Bilgi durumları ne anlama geliyor?',
      'context.information_status_guide.helper':
          'Durum bilgi bloğuna aittir; bağlı kaynağı ayrıca doğrulamaz.',
      'context.information_status_guide.verified_desc':
          'Editoryal kayıt bu bloğun doğrulandığını göstermektedir.',
      'context.information_status_guide.claimed_desc':
          'Bu blok bir iddia içermekte ve doğrulanmış olarak işaretlenmemiştir.',
      'context.information_status_guide.disputed_desc':
          'Mevcut kayıt bu blok hakkında çelişkili bilgiler içermektedir.',
      'context.information_status_guide.unknown_desc':
          'Mevcut kayıt bu blok için bir durum belirlememiştir.',
      'context.source.official': 'Resmî kaynak',
      'context.source.news': 'Haber kaynağı',
      'context.source.research': 'Araştırma',
      'context.source.editorial': 'Editoryal kaynak',
      'context.source.other': 'Diğer kaynak',
      'common.loading': 'Hazırlanıyor…',
      'common.retry': 'Tekrar dene',
      'common.start': 'Başla',
      'decision.commit': 'Kararımı Ver',
      'decision.retry_sync': 'Kararımı Senkronize Et',
      'decision.commit_helper': 'Kararını kilitle ve sonucu gör.',
      'decision.complete_required':
          'Devam etmek için zorunlu soruları yanıtla.',
      'decision.required_question': 'Zorunlu',
      'decision.optional_question': 'İsteğe bağlı',
      'decision.unsupported_question_type':
          'Bu soru tipi bu sürümde desteklenmiyor.',
      'reason.title': 'Neden böyle düşündün?',
      'reason.helper':
          'İstersen kararında etkili olan gerekçeleri seç. Bu sürümde gerekçen diğer kullanıcılara gösterilmez; kısa metin güvenlik amacıyla incelenebilir.',
      'reason.selection_limit': 'En fazla {maxTags} gerekçe seçebilirsin.',
      'reason.text_label': 'Kısa gerekçe',
      'reason.text_hint': 'İstersen kendi cümlelerinle ekle…',
      'reason.tag.fairness': 'Adalet',
      'reason.tag.need': 'İhtiyaç',
      'reason.tag.responsibility': 'Sorumluluk',
      'reason.tag.empathy': 'Empati',
      'reason.tag.rules': 'Kural',
      'reason.tag.consequence': 'Sonuç',
      'reason.tag.proportionality': 'Orantılılık',
      'reason.tag.practical_impact': 'Pratik etki',
      'sync.pending_helper':
          'Kararın cihazda güvende. Aynı karar anahtarıyla güvenli biçimde yeniden denenecek.',
      'sync.offline_draft': 'Çevrimdışı taslak geri yüklendi.',
      'sync.decision_pending':
          'Yanıtların ve gerekçen cihazda güvende. Bağlantı geldiğinde Commit öncesi senkronizasyon yeniden denenecek.',
      'sync.reveal_pending':
          'Kararın kaydedildi. Sonuç bağlantı geldiğinde yeniden açılabilir.',
      'sync.uncertain_commit':
          'Bağlantı kesildi. Kararın gönderilmiş olabilir; aynı anahtarla güvenli biçimde kontrol edeceğiz.',
      'reveal.title': 'Topluluk nasıl tarttı?',
      'reveal.trusted_sample': 'Güvenilir örneklem',
      'reveal.select_answer': 'Bir seçenek seç',
      'reflection.title': 'Kararına bir daha bak',
      'reflection.decision_changed':
          'İki kararın arasında {count} yanıt değişti.',
      'reflection.decision_unchanged':
          'İki kararın arasında yanıt değişikliği görünmüyor.',
      'reflection.intervention_summary':
          'İki kararın arasında {count} kayıtlı karşılaşma bulunuyor.',
      'reflection.non_causal_note':
          'Bu görünüm değişimi ve aradaki karşılaşmaları birlikte gösterir; bir karşılaşmanın karar değişimine neden olduğunu söylemez.',
      'reflection.complete': 'Yansımayı tamamla',
      'reflection.completed': 'Yansıma tamamlandı',
      'reflection.loading': 'Yansıma hazırlanıyor…',
      'reflection.retry': 'Yansımayı tekrar yükle',
      'flow.capability_pending.title': 'Bu adım henüz kullanıma açılmadı',
      'flow.capability_pending.decision_revision':
          'Bu akışta yeniden tartım adımı var. Karar değişimi altyapısı tamamlandığında aynı akış içinde açılacak.',
      'flow.capability_pending.reflection_runtime':
          'Bu akışın yansıtma adımı hazırlanıyor. Mevcut kararın değiştirilmedi.',
      'flow.capability_pending.default':
          'Akış bu adımı tanıyor ancak bu sürüm henüz çalıştırmıyor. Diğer desteklenen adımlar aynı akışta kullanılabilir.',
      'flow.offline_unavailable':
          'Bu eski çevrimdışı taslakta doğrulanmış akış bilgisi yok. Bağlantı kurulunca akış sunucudan yeniden alınacak; uygulama varsayılan bir ekran dizisi uydurmayacak.',
      'flow.runtime_unavailable':
          'Bu vaka için doğrulanmış karar akışı şu anda kullanılamıyor.',
      'flow.runtime_mismatch':
          'Karar akışı bu oturumun vaka sürümüyle eşleşmedi. Güvenli biçimde yeniden yükle.',
      'perspective.title': 'Başka açılardan bak',
      'perspective.loading': 'Perspektifler hazırlanıyor…',
      'perspective.retry': 'Perspektifleri tekrar yükle',
      'perspective.unavailable':
          'Sonucun hazır. Perspektifler şu anda yüklenemedi; kararını yeniden göndermeden tekrar deneyebilirsin.',
      'perspective.curated_note':
          'Şimdilik doğrulanmış editoryal perspektifler gösteriliyor.',
      'perspective.cluster_pending':
          'Mevcut perspektifleri görebilirsin; daha geniş perspektif işlemesi sürüyor.',
      'perspective.empty':
          'Bu vaka için şu anda uygun bir karşı perspektif yok.',
      'perspective.reason_pending_moderation':
          'Kendi kısa gerekçen güvenlik incelemesinde. Bu, aşağıdaki perspektiflerin kaynağı olduğu anlamına gelmez.',
      'perspective.methodology': 'Bu görünüm hakkında',
      'perspective.slot.near': 'Yakın perspektif',
      'perspective.slot.opposing': 'Karşı perspektif',
      'perspective.slot.bridge': 'Köprü perspektifi',
      'perspective.slot.alternative_context': 'Alternatif bağlam',
      'perspective.source.curated': 'Editoryal olarak derlendi',
      'perspective.source.human_reason': 'İnsan gerekçesi',
      'perspective.source.default': 'Kaynak bilgisi',
      'error.generic':
          'Bir sorun oluştu. Kararın kaybolmadı; tekrar deneyebilirsin.',
      'error.network_unavailable':
          'Bağlantı kurulamadı. Cihazdaki karar korunuyor.',
      'error.guest_continuity_required':
          'Bu misafir oturumu artık yenilenemiyor. KEFE kimliği sessizce yeni bir kimlikle değiştirmedi.',
      'error.account_reauthentication_required':
          'Bu hesap oturumu sona erdi. Geçmişe yeniden erişmek için hesabını tekrar doğrula.',
      'error.legacy_continuity_required':
          'Bu eski oturum güvenli biçimde yükseltilemedi. KEFE yerine yeni bir misafir kimliği oluşturmadı.',
      'signal.card_eyebrow': 'TOPLUMSAL UZLAŞI SİNYALİ',
      'signal.tier_gold': 'Altın Uzlaşı (Yüksek Güvenilirlik)',
      'signal.tier_silver': 'Gümüş Uzlaşı (Doğrulanmış Örneklem)',
      'signal.tier_bronze': 'Bronz Uzlaşı (Gelişen Sinyal)',
      'signal.agreement_badge': '%{pct} Uzlaşı (n={count})',
      'signal.provisional_label': 'EDİTÖRYEL İNCELEME BEKLİYOR',
      'institution.eyebrow': 'DOĞRULANMIŞ KURUM YANITI',
      'institution.verified_badge': 'Resmi & Doğrulanmış',
      'institution.milestone_label': 'Hedef takvim: {date}',
      'institution.type_acknowledge': 'Resmi Tebellüğ & Kayıt',
      'institution.type_commitment': 'Bağlayıcı Taahhüt',
      'institution.type_policy_change': 'Mevzuat / Politika Değişikliği',
      'institution.type_clarification': 'Maddi Olgu Açıklaması',
      'institution.type_decline': 'Gerekçeli Yanıt Vermeme',
      'retry_action': 'Tekrar Dene',
      // Signal screen
      'signal_screen.title': 'Sinyaller',
      'signal_screen.subtitle': 'Nitelik eşiklerini gecen kolektif kararlar.',
      'signal_screen.methodology_note': 'Kolektif sonuc otomatik olarak Sinyal veya gercek sayilmaz. Her kart olcek, butunluk ve metodoloji kapilalarindan gecmistir.',
      'signal_screen.load_error': 'Sinyaller yuklenemedi. Lutfen tekrar deneyin.',
      'signal_screen.empty': 'Henuz nitelikli sinyal yok. Kolektif sonuclar eslikleri karsiladiginda sinyaller burada gorulur.',
      'signal_screen.provisional_label': 'EDITORYAL INCELEME BEKLIYOR',

      // Impact screen
      'impact.title': 'Etki',
      'impact.subtitle': 'Kurumlara ulaşan ve eylem başlatan nitelikli sinyaller.',
      'impact.institution_responses_title': 'Kurumsal Yanıtlar',
      'impact.actions_title': 'Eylem Adımları',
      'impact.load_error': 'Etki verileri yüklenemedi. Lütfen tekrar deneyin.',
      'impact.no_responses': 'Henüz kurumsal yanıt yok. Nitelikli sinyaller burada görünecek.',
      'impact.no_actions': 'Henüz eylem adımı kaydedilmedi.',
      'impact.methodology_note': 'Kolektif sonuç otomatik olarak Sinyal, gerçek veya otorite sayılmaz. Bu ekrana ulaşan sinyaller ölçek, bütünlük ve metodoloji eşiklerini geçmiştir.',
      // About screen
      'about.title': 'KEFE Hakkında',
      'about.methodology_title': 'Metodoloji',
      'about.commit_first': 'Commit First',
      'about.commit_first_desc': 'Başkalarının ne düşündüğünü görmeden kararını verirsin. Bu, sosyal baskıyı ve sürü etkisini engeller.',
      'about.blind_first': 'Blind First',
      'about.blind_first_desc': 'Sonuçlar ve perspektifler yalnızca taahhüdünden sonra görünür. Ön-sonuç izolasyonu hem ürün özelliği hem gizlilik güvencesidir.',
      'about.signal_title': 'Sinyal → Etki',
      'about.signal_desc': 'Her kolektif sonuç Sinyal değildir. Sinyallerin kurumlara ulaşabilmesi için ölçek, bütünlük ve metodoloji eşiklerini geçmesi gerekir.',
      'about.version_label': 'v2.0 · 2026-09-13',
    },
  };
}
