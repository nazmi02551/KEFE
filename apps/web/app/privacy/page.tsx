import type { Metadata } from "next";
import Link from "next/link";

import styles from "@/app/privacy/page.module.css";

const _siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://kefe.app";

export const metadata: Metadata = {
  title: "Gizlilik Politikası",
  description:
    "KEFE gizlilik politikası — KVKK ve GDPR uyumlu veri işleme, saklama ve silme hakları.",
  openGraph: {
    title: "Gizlilik Politikası · KEFE",
    description: "KVKK ve GDPR uyumlu. Verilerinizi kontrol edin.",
    url: `${_siteUrl}/privacy`,
    type: "website",
  },
  robots: {
    index: true,
    follow: false, // Privacy pages shouldn't be heavily indexed
  },
};

interface Section {
  id: string;
  title: string;
  content: string;
}

const PRIVACY_SECTIONS: Section[] = [
  {
    id: "collection",
    title: "Hangi verileri topluyoruz?",
    content:
      "KEFE, taahhüt ettiğiniz kararları (commit), katıldığınız meseleleri ve uygulama içi etkileşimlerinizi kaydeder. Bireysel kararınız şifrelenmiş ve izole halde saklanır. Kimlik doğrulama için e-posta veya telefon numarası kullanılabilir; bu veriler OTP akışında şifreli olarak işlenir.",
  },
  {
    id: "usage",
    title: "Veriler nasıl kullanılır?",
    content:
      "Kişisel verileriniz yalnızca platform işlevselliği için kullanılır: meseleye katılımınız, sinyal üretimi ve kişisel ilerleme takibi. Verileriniz üçüncü taraflarla paylaşılmaz, pazarlama veya reklam amacıyla kullanılmaz. Kolektif analizler anonimleştirilmiş toplu veriden üretilir.",
  },
  {
    id: "isolation",
    title: "Commit First izolasyonu",
    content:
      "Kararınız taahhüt edilmeden önce kolektif sonuçla hiçbir şekilde karşılaştırılmaz. Ön-sonuç izolasyonu hem metodolojik hem de teknik bir güvencedir. Taahhüt öncesi bireysel cevabınız hiçbir analitik sisteme aktarılmaz.",
  },
  {
    id: "inference",
    title: "Nedensel çıkarım yapılmıyor",
    content:
      "KEFE, davranışsal veya kişisel verilerden kişilik, ideoloji, psikometri veya nedensel tahmin üretmez. My KEFE görünümleri yalnızca gözlemsel veriye — sizin kendi kararlarınızın izine — dayanır.",
  },
  {
    id: "rights",
    title: "KVKK ve GDPR haklarınız",
    content:
      "Kişisel verilerinize erişim, düzeltme, taşıma ve silme haklarına sahipsiniz. Veri dışa aktarma ve hesap silme işlemleri uygulama içinden yapılabilir. Hesap silindiğinde kişisel verileriniz kalıcı olarak anonimleştirilir; aggregate sinyal katkıları anonimleştirilmiş halde kalabilir.",
  },
  {
    id: "retention",
    title: "Saklama süreleri",
    content:
      "Aktif hesaplar için veriler hesap aktif olduğu sürece saklanır. Hesap silme talebinden sonra kişisel veriler en geç 30 gün içinde kaldırılır. Anonimleştirilmiş kolektif analiz verileri saklama süresinden muaftır.",
  },
  {
    id: "contact",
    title: "İletişim",
    content:
      "Gizlilikle ilgili sorularınız için privacy@kefe.app adresine yazabilirsiniz. Tüm talepler KVKK/GDPR gereklilikleri çerçevesinde en geç 30 gün içinde yanıtlanır.",
  },
];

export default function PrivacyPage() {
  return (
    <main className={styles.main}>
      <header className={styles.header}>
        <h1 className={styles.title}>Gizlilik Politikası</h1>
        <p className={styles.meta}>
          Son güncelleme: Temmuz 2026 · KVKK ve GDPR uyumlu
        </p>
        <p className={styles.intro}>
          KEFE, katılımcıların gizliliğini metodolojisinin bir parçası olarak
          tasarlar. Commit First izolasyonu hem bir ürün özelliği hem de bir
          gizlilik güvencesidir.
        </p>
      </header>

      <nav className={styles.toc} aria-label="İçindekiler">
        <p className={styles.tocTitle}>İçindekiler</p>
        <ol className={styles.tocList}>
          {PRIVACY_SECTIONS.map((s) => (
            <li key={s.id}>
              <a href={`#${s.id}`} className={styles.tocLink}>
                {s.title}
              </a>
            </li>
          ))}
        </ol>
      </nav>

      <article className={styles.article}>
        {PRIVACY_SECTIONS.map((s) => (
          <section key={s.id} id={s.id} className={styles.section}>
            <h2 className={styles.sectionTitle}>{s.title}</h2>
            <p className={styles.sectionContent}>{s.content}</p>
          </section>
        ))}
      </article>

      <footer className={styles.footer}>
        <nav className={styles.footerNav}>
          <Link href="/faq" className={styles.footerLink}>
            SSS →
          </Link>
          <Link href="/about" className={styles.footerLink}>
            Metodoloji →
          </Link>
        </nav>
      </footer>
    </main>
  );
}