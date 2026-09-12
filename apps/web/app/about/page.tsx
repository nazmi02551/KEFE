import type { Metadata } from "next";
import Link from "next/link";

import styles from "@/app/about/page.module.css";

const _siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://kefe.app";

export const metadata: Metadata = {
  title: "Hakkında",
  description:
    "KEFE metodolojisi: Commit First, Blind First, Kolektif Sonuç, Signal ve Impact. Neden farklı?",
  openGraph: {
    title: "KEFE Hakkında — Metodoloji",
    description:
      "Commit First, Blind First — sesiniz nitelendiriliyor. KEFE'nin metodoloji farkı.",
    url: `${_siteUrl}/about`,
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "KEFE Hakkında",
    description: "Commit First, Blind First ile methodology-qualified civic deliberation.",
  },
};

interface MethodologyPrincipleProps {
  label: string;
  title: string;
  description: string;
  color?: "gold" | "cyan";
}

function MethodologyPrinciple({
  label,
  title,
  description,
  color = "gold",
}: MethodologyPrincipleProps) {
  return (
    <article className={styles.principle} data-color={color}>
      <span className={styles.principleLabel}>{label}</span>
      <h2 className={styles.principleTitle}>{title}</h2>
      <p className={styles.principleDesc}>{description}</p>
    </article>
  );
}

export default function AboutPage() {
  return (
    <main className={styles.main}>
      {/* Hero */}
      <section className={styles.hero}>
        <h1 className={styles.heroTitle}>
          <span className={styles.heroTitleKefe}>KEFE</span> Nedir?
        </h1>
        <p className={styles.heroParagraph}>
          KEFE, kolektif sesin kurumsal etkiye dönüştüğü, methodology-qualified
          bir sivil katılım platformudur. Oy anketlerinden farklı olarak KEFE,
          her katılımı metodolojik olarak nitelendirir ve{" "}
          <strong>yalnızca nitelikli katılımları</strong> sinyal olarak kabul eder.
        </p>
      </section>

      {/* Core principles */}
      <section className={styles.principles}>
        <h2 className={styles.sectionTitle}>Temel Metodoloji Prensipleri</h2>

        <MethodologyPrinciple
          label="1. Prensip"
          title="Commit First"
          color="gold"
          description="Katılımcı önce kendi kararını taahhüt eder — kolektif sonucu görmeden. Bu, sosyal baskı, sürü etkisi ve onaylama önyargısını metodolojik olarak engeller. Taahhüt geri alınamaz; bu güvence, katılımın bütünlüğünü korur."
        />

        <MethodologyPrinciple
          label="2. Prensip"
          title="Blind First"
          color="cyan"
          description="Kolektif sonuç, kişi kendi cevabını taahhüt etmeden açılmaz. Kör protokol, ön-sonuç izolasyonunu güvence altına alır. Sonucu görmek için taahhüt şarttır — bu, platformun temel sözleşmesidir."
        />

        <MethodologyPrinciple
          label="3. Prensip"
          title="Kolektif Sonuç ≠ Otomatik Sinyal"
          color="gold"
          description="Katılımcıların toplu kararı, doğrudan sinyal olarak kabul edilmez. Kolektif sonuç bir gözlemdir; sinyal olabilmesi için nitelik, ölçek ve bütünlük eşiklerini geçmesi gerekir. Gerçek veya otorite de değildir."
        />

        <MethodologyPrinciple
          label="4. Prensip"
          title="Signal → Impact"
          color="cyan"
          description="Nitelikli kolektif ses, kurumsal yanıt mekanizmasına bağlanır. Sinyal; ilgili kurum, belediye veya politika yapıcıya iletilir. Etki takibi kamuya açıktır — kurumsal yanıtlar ve eylem kilometre taşları şeffaf biçimde yayımlanır."
        />

        <MethodologyPrinciple
          label="5. Prensip"
          title="My KEFE: Gözlemsel, Nedensel Değil"
          color="gold"
          description="Kişisel KEFE görünümleri yalnızca gözlemsel veriye dayanır. Kişilik, ideoloji, psikometri veya nedensel çıkarım yapılmaz. Platformun sizi 'anlaması' değil, kendi kararlarınızın niteliksel izini tutması hedeflenir."
        />
      </section>

      {/* Methodology chain */}
      <section className={styles.chain}>
        <h2 className={styles.sectionTitle}>Katılım Zinciri</h2>
        <ol className={styles.chainList}>
          <li className={styles.chainStep}>
            <span className={styles.chainNumber}>01</span>
            <div>
              <strong>Mesele</strong> — Gerçek bir toplumsal denge noktası. Editöryal süreçle nitelendirilir.
            </div>
          </li>
          <li className={styles.chainStep}>
            <span className={styles.chainNumber}>02</span>
            <div>
              <strong>Commit First Katılım</strong> — Kör protokol ile metodolojik taahhüt.
            </div>
          </li>
          <li className={styles.chainStep}>
            <span className={styles.chainNumber}>03</span>
            <div>
              <strong>Perspektif Açılımı</strong> — Taahhüt sonrası kolektif görünüm ve ağırlıklı perspektifler.
            </div>
          </li>
          <li className={styles.chainStep}>
            <span className={styles.chainNumber}>04</span>
            <div>
              <strong>Sinyal Nitelendirmesi</strong> — Ölçek, bütünlük ve metodoloji eşikleri karşılandığında sinyal üretilir.
            </div>
          </li>
          <li className={styles.chainStep}>
            <span className={styles.chainNumber}>05</span>
            <div>
              <strong>Impact</strong> — Sinyal ilgili kuruma iletilir; yanıt ve eylem kilometre taşları kamuya açıktır.
            </div>
          </li>
        </ol>
      </section>

      {/* CTA */}
      <section className={styles.cta}>
        <p className={styles.ctaText}>
          Metodoloji hakkında daha fazla bilgi edinmek veya aktif meselelere katılmak için:
        </p>
        <nav className={styles.ctaNav}>
          <Link href="/cases" className={styles.ctaPrimary}>
            Meseleleri İncele
          </Link>
          <Link href="/signal" className={styles.ctaSecondary}>
            Sinyal Kartları
          </Link>
        </nav>
      </section>
    </main>
  );
}