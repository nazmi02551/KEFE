import '../../../core/localization/kefe_locale_catalog.dart';

abstract final class ProgressStringCatalog {
  static const KefeLocaleResources resources = {
    'tr': {
      'progress.title': 'Benim Kefem',
      'progress.loading': 'Tartım geçmişin hazırlanıyor…',
      'progress.unavailable':
          'Sonucun hazır. Kişisel ilerleme şu anda yüklenemedi.',
      'progress.retry': 'İlerlemeyi tekrar yükle',
      'progress.weighs': 'Tartım',
      'progress.cases': 'Vaka',
      'progress.domains': 'Alan',
      'progress.recent': 'Son tamamlananlar',
      'progress.methodology':
          'Bu görünüm yalnızca kendi tamamlanmış tartımlarına dayanır; kişilik veya ideoloji çıkarımı yapılmaz.',
      'progress.readiness.forming': 'Karar geçmişin oluşmaya başladı.',
      'progress.readiness.default':
          'Tartım yaptıkça karar geçmişin burada büyüyecek.',
      'journey.eyebrow': 'MY KEFE',
      'journey.title': 'Karar yolculuğun.',
      'journey.subtitle':
          'Yalnızca KEFE’de kaydedilen tartım, yeniden tartım ve yansıma geçmişin.',
      'journey.preview_notice':
          'Bu ekrandaki geçmiş Product Preview için hazırlanmış örnek veridir.',
      'journey.revisits': 'Yeniden tartım',
      'journey.reflections': 'Yansıma',
      'journey.domain_activity': 'Tartım alanların',
      'journey.recent': 'Son karar yolculukların',
      'journey.revisited': 'Yeniden tartıldı',
      'journey.reflected': 'Yansıma tamamlandı',
      'journey.committed': 'İlk karar kaydedildi',
      'journey.empty':
          'Henüz tamamlanmış bir tartım yok. İlk kararın burada görünmeye başlayacak.',
      'journey.non_inference_note':
          'Bu özet yalnızca gözlenen uygulama geçmişini gösterir; kişilik, ideoloji, psikolojik profil veya neden-sonuç çıkarımı yapmaz.',
      'journey.weigh_count': '{count} tartım',
      'journey.update_count.one': '{count} yeniden tartım',
      'journey.update_count.many': '{count} yeniden tartım',
      'account.offer.title': 'İlerlemeni gelecekte de koru',
      'account.offer.body':
          'KEFE hesabı, ilerlemeni cihaz değişikliklerinde korumak için kullanılabilecek. Misafir olarak devam etmek her zaman mümkün.',
      'account.offer.unavailable':
          'Hesap oluşturma henüz açılmadı; çalışmayan bir kayıt adımı göstermiyoruz.',
    },
    'en': {
      'progress.title': 'My KEFE',
      'progress.loading': 'Preparing your weigh history…',
      'progress.unavailable':
          'Your result is ready. Personal progress could not load right now.',
      'progress.retry': 'Retry progress',
      'progress.weighs': 'Weighs',
      'progress.cases': 'Cases',
      'progress.domains': 'Domains',
      'progress.recent': 'Recently completed',
      'progress.methodology':
          'This view uses only your completed weighs. It does not infer personality or ideology.',
      'progress.readiness.forming':
          'Your decision history is beginning to take shape.',
      'progress.readiness.default':
          'Your decision history will grow here as you complete weighs.',
      'journey.eyebrow': 'MY KEFE',
      'journey.title': 'Your decision journey.',
      'journey.subtitle':
          'Only your recorded KEFE weigh, revisit and reflection history.',
      'journey.preview_notice':
          'History on this screen is example data prepared for Product Preview.',
      'journey.revisits': 'Revisits',
      'journey.reflections': 'Reflections',
      'journey.domain_activity': 'Your weigh activity',
      'journey.recent': 'Recent decision journeys',
      'journey.revisited': 'Revisited',
      'journey.reflected': 'Reflection completed',
      'journey.committed': 'Initial decision recorded',
      'journey.empty':
          'No completed weighs yet. Your first decision will begin your history here.',
      'journey.non_inference_note':
          'This summary only shows observed product history; it does not infer personality, ideology, psychological traits or causality.',
      'journey.weigh_count': '{count} weighs',
      'journey.update_count.one': '{count} revisit',
      'journey.update_count.many': '{count} revisits',
      'account.offer.title': 'Protect your progress for the future',
      'account.offer.body':
          'A KEFE account can later protect your progress across device changes. Continuing as a guest always remains available.',
      'account.offer.unavailable':
          'Account creation is not available yet, so no non-functional sign-up action is shown.',
    },
  };
}
