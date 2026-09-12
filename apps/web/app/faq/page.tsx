import type { Metadata } from "next";
import Link from "next/link";

import styles from "@/app/faq/page.module.css";

const _siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://kefe.app";

export const metadata: Metadata = {
  title: "SSS — Sıkça Sorulan Sorular",
  description:
    "KEFE hakkında sıkça sorulan sorular: Commit First, gizlilik, veri, sinyal nitelendirmesi.",
  openGraph: {
    title: "SSS · KEFE",
    description: "Commit First, gizlilik, sinyal ve metodoloji hakkında sorular.",
    url: `${_siteUrl}/faq`,
    type: "website",
  },
};

interface FaqItem {
  question: string;
  answer: string;
}

const FAQ_ITEMS: FaqItem[] = [
  {
    question: "KEFE nedir?",
    answer:
      "KEFE, kolektif sesin kurumsal etkiye dönüştüğü methodology-qualified bir sivil katılım platformudur. Oy anketlerinin aksine KEFE, her katılımı metodolojik olarak nitelendirir.",
  },
  {
    question: "Commit First ne anlama geliyor?",
    answer:
      "Kolektif sonucu görmeden önce kendi kararınızı taahhüt etmeniz gerekir. Bu protokol, sosyal baskıyı, sürü etkisini ve onaylama önyargısını metodolojik olarak engeller. Taahhüdünüz geri alınamaz.",
  },
  {
    question: "Kararım kimlerle paylaşılıyor?",
    answer:
      "Bireysel kararınız hiçbir zaman başkalarına açıklanmaz. Kolektif sonuç, taahhüt eden tüm katılımcıların anonim katkısından oluşur. Gizlilik politikamıza /privacy adresinden ulaşabilirsiniz.",
  },
  {
    question: "Sinyal ile kolektif sonuç arasındaki fark nedir?",
    answer:
      "Kolektif sonuç, katılımcıların toplu kararını gösterir — bu ham bir gözlemdir. Sinyal ise ölçek, bütünlük ve metodoloji eşiklerini geçtikten sonra üretilen nitelikli bir çıktıdır. Her kolektif sonuç otomatik olarak sinyal değildir.",
  },
  {
    question: "Sinyal kurumsal bir etkiye nasıl dönüşüyor?",
    answer:
      "Nitelikli sinyal, ilgili kurum, belediye veya politika yapıcıya iletilir. Kurumsal yanıtlar ve eylem kilometre taşları /impact sayfasında kamuya açık biçimde yayımlanır.",
  },
  {
    question: "My KEFE profilim ne gösteriyor?",
    answer:
      "My KEFE yalnızca gözlemsel veriye dayanır: hangi meselelere katıldığınız, ne zaman, taahhüdünüzün kolektif perspektiflerle nasıl örtüştüğü. Kişilik analizi, ideoloji çıkarımı, psikometri veya nedensel yorumlama yapılmaz.",
  },
  {
    question: "Verilerimi silebilir miyim?",
    answer:
      "Evet. KEFE, KVKK ve GDPR uyumlu veri silme hakkı sunar. Kişisel verilerinizin tamamını dışa aktarabilir ve hesabınızı kalıcı olarak silebilirsiniz. Bu işlemler uygulama içinden yapılabilir.",
  },
  {
    question: "Platform ücretsiz mi?",
    answer:
      "Temel katılım tamamen ücretsizdir. Premium özellikler (gelişmiş perspektif analizi, sinyal arşivi, etki takibi) ayrı bir abonelikle sunulacaktır.",
  },
  {
    question: "Hangi diller destekleniyor?",
    answer:
      "KEFE şu anda Türkçe ve İngilizce olarak kullanılabilir. Dil seçimi uygulamadan yapılabilir.",
  },
  {
    question: "Mesele nasıl önerilebilir?",
    answer:
      "Mesele önerme süreci editöryal değerlendirme gerektirir. Uygulama içindeki 'Mesele Öner' akışını kullanarak başvurabilirsiniz. Tüm meseleler metodolojik uygunluk, ölçeklenebilirlik ve gerçek denge noktası kriterlerine göre değerlendirilir.",
  },
];

export default function FaqPage() {
  return (
    <main className={styles.main}>
      <header className={styles.header}>
        <h1 className={styles.title}>Sıkça Sorulan Sorular</h1>
        <p className={styles.subtitle}>
          KEFE metodolojisi, gizlilik ve platform kullanımı hakkında.
        </p>
      </header>

      <ol className={styles.faqList}>
        {FAQ_ITEMS.map((item, idx) => (
          <li key={idx} className={styles.faqItem}>
            <h2 className={styles.question}>{item.question}</h2>
            <p className={styles.answer}>{item.answer}</p>
          </li>
        ))}
      </ol>

      <footer className={styles.footer}>
        <p className={styles.footerText}>
          Cevabını bulamadığınız bir soru var mı?
        </p>
        <nav className={styles.footerNav}>
          <Link href="/about" className={styles.footerLink}>
            Metodoloji sayfasına git →
          </Link>
          <Link href="/privacy" className={styles.footerLink}>
            Gizlilik politikası →
          </Link>
        </nav>
      </footer>
    </main>
  );
}