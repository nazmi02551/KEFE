import type { Route } from "next";
import Link from "next/link";

import styles from "@/app/home.module.css";
import { EditorialWorkspace } from "@/src/components/editorial-workspace";

export default function AdminStudioPage() {
  return (
    <>
      <EditorialWorkspace />
      <section className={styles.moduleSection} aria-label="Admin Studio Çalışma Alanları">
        <div className={styles.moduleHeader}>
          <h2>Yönetim ve Operasyon Modülleri</h2>
          <p>
            KEFE Admin Studio bünyesindeki tüm editoryal, kalite denetim ve operasyonel modüllere doğrudan erişin.
          </p>
        </div>
        <div className={styles.moduleGrid}>
          <Link href="/case-builder" className={styles.moduleCard}>
            <span className={styles.moduleBadge}>CAP-063 · Authoring</span>
            <h3 className={styles.moduleTitle}>Vaka Oluşturucu (Case Builder)</h3>
            <p className={styles.moduleDesc}>
              Content Authoring DRAFT sürümlerini oluşturun, düzenleyin ve doğrulayın.
            </p>
            <span className={styles.moduleAction}>Modülü Aç →</span>
          </Link>
          <Link href="/content-review" className={styles.moduleCard}>
            <span className={styles.moduleBadge}>CAP-065 · Quality Gate</span>
            <h3 className={styles.moduleTitle}>Editoryal Kalite İncelemesi</h3>
            <p className={styles.moduleDesc}>
              IN_REVIEW durumundaki vakaların bağımsız kalite kontrol ve onay süreçleri.
            </p>
            <span className={styles.moduleAction}>Modülü Aç →</span>
          </Link>
          <Link href="/flow-composer" className={styles.moduleCard}>
            <span className={styles.moduleBadge}>CAP-064 · Flow Engine</span>
            <h3 className={styles.moduleTitle}>Akış Bestecisi (Flow Composer)</h3>
            <p className={styles.moduleDesc}>
              Karar akış şablonlarını, adımları ve dallanma yapılandırmalarını yönetin.
            </p>
            <span className={styles.moduleAction}>Modülü Aç →</span>
          </Link>
          <Link href="/publication-operations" className={styles.moduleCard}>
            <span className={styles.moduleBadge}>CAP-066 · Operations</span>
            <h3 className={styles.moduleTitle}>Yayın Operasyonları</h3>
            <p className={styles.moduleDesc}>
              Onaylanmış vakaların yayına alınması (publish) ve gerekçeli geri çekilmesi.
            </p>
            <span className={styles.moduleAction}>Modülü Aç →</span>
          </Link>
          <Link href="/reason-moderation" className={styles.moduleCard}>
            <span className={styles.moduleBadge}>CAP-066 · Moderation</span>
            <h3 className={styles.moduleTitle}>Topluluk Gerekçe Moderasyonu</h3>
            <p className={styles.moduleDesc}>
              Kullanıcıların sunduğu karar gerekçelerini ve bayraklanan içerikleri denetleyin.
            </p>
            <span className={styles.moduleAction}>Modülü Aç →</span>
          </Link>
          <Link href="/operational-reports" className={styles.moduleCard}>
            <span className={styles.moduleBadge}>CAP-041 / CAP-078 · Analytics</span>
            <h3 className={styles.moduleTitle}>Operasyonel Raporlar</h3>
            <p className={styles.moduleDesc}>
              Sistem genelindeki sinyal, metrik, dağılım ve operasyonel özetler.
            </p>
            <span className={styles.moduleAction}>Modülü Aç →</span>
          </Link>
          <Link href="/case-media" className={styles.moduleCard}>
            <span className={styles.moduleBadge}>CAP-034 · Assets</span>
            <h3 className={styles.moduleTitle}>Vaka Medya Kaydı</h3>
            <p className={styles.moduleDesc}>
              Doğrulanmış görsel ve medya varlıklarının içerik karması ile kayıt yönetimi.
            </p>
            <span className={styles.moduleAction}>Modülü Aç →</span>
          </Link>
          <Link href="/signal" className={styles.moduleCard}>
            <span className={styles.moduleBadge}>CAP-042..048 · Signal</span>
            <h3 className={styles.moduleTitle}>Sinyal Operasyonları</h3>
            <p className={styles.moduleDesc}>
              Kolektif uzlaşı, metodoloji sertifikasyonu, katkı sınıfları ve sinyal hedef sicili.
            </p>
            <span className={styles.moduleAction}>Modülü Aç →</span>
          </Link>
          <Link href="/impact" className={styles.moduleCard}>
            <span className={styles.moduleBadge}>CAP-049..054 · Impact</span>
            <h3 className={styles.moduleTitle}>Etki & Kurumsal Yanıt</h3>
            <p className={styles.moduleDesc}>
              Doğrulanmış kurum yanıtları, eylem adımları ve kilometre taşı takibi.
            </p>
            <span className={styles.moduleAction}>Modülü Aç →</span>
          </Link>
          <Link href="/deliberation" className={styles.moduleCard}>
            <span className={styles.moduleBadge}>CAP-075 / 068 / 072 · Audit</span>
            <h3 className={styles.moduleTitle}>Deliberation & Kalite Denetimi</h3>
            <p className={styles.moduleDesc}>
              8 boyutlu kalite kontrolü, halk itirazları yönetimi ve şeffaf vaka düzeltme geçmişi.
            </p>
            <span className={styles.moduleAction}>Modülü Aç →</span>
          </Link>
          <Link href="/claims" className={styles.moduleCard}>
            <span className={styles.moduleBadge}>CAP-057..059 · Knowledge</span>
            <h3 className={styles.moduleTitle}>İddia & Bilgi Grafiği</h3>
            <p className={styles.moduleDesc}>
              Birinci sınıf iddia sınıflandırması, kanıt değerlendirme döngüsü ve iddia-argüman ağ ilişkileri.
            </p>
            <span className={styles.moduleAction}>Modülü Aç →</span>
          </Link>
          <Link href={"/trust-integrity" as Route} className={styles.moduleCard}>
            <span className={styles.moduleBadge}>CAP-073 · Trust & Integrity</span>
            <h3 className={styles.moduleTitle}>Bot Kalkanı & Gündem Eşiği</h3>
            <p className={styles.moduleDesc}>
              Sentetik astroturfing tespiti, bot koordinasyon karantinası ve dinamik gündem önceliklendirme.
            </p>
            <span className={styles.moduleAction}>Modülü Aç →</span>
          </Link>
          <Link href={"/analytics" as Route} className={styles.moduleCard}>
            <span className={styles.moduleBadge}>CAP-114..117 · Analytics</span>
            <h3 className={styles.moduleTitle}>North Star & Kutuplaşma Metrikleri</h3>
            <p className={styles.moduleDesc}>
              Meaningful Weighs / WAU, aktivasyon dönüşüm hunisi ve kutuplaşma azaltma endeksi.
            </p>
            <span className={styles.moduleAction}>Modülü Aç →</span>
          </Link>
          <Link href={"/ai-editorial" as Route} className={styles.moduleCard}>
            <span className={styles.moduleBadge}>CAP-060 · Content Admin</span>
            <h3 className={styles.moduleTitle}>AI Editoryal Asistan</h3>
            <p className={styles.moduleDesc}>
              Yapay zeka destekli iddia çıkarımı, dengeli perspektif önerileri ve önyargı denetimi.
            </p>
            <span className={styles.moduleAction}>Modülü Aç →</span>
          </Link>
          <Link href={"/finops" as Route} className={styles.moduleCard}>
            <span className={styles.moduleBadge}>CAP-124 · FinOps</span>
            <h3 className={styles.moduleTitle}>FinOps & Birim Maliyet Analitiği</h3>
            <p className={styles.moduleDesc}>
              Tartım başına maliyet (CPW), model token tüketimi, SMS/OTP giderleri ve ölçek projeksiyonu.
            </p>
            <span className={styles.moduleAction}>Modülü Aç →</span>
          </Link>
          <Link href={"/radar-live" as Route} className={styles.moduleCard}>
            <span className={styles.moduleBadge}>CAP-076 · Consumer Growth</span>
            <h3 className={styles.moduleTitle}>Canlı Radar & Bağlam Sapması</h3>
            <p className={styles.moduleDesc}>
              Gerçek zamanlı tartışma momentumu, demografik yönelim vektörleri ve yasal sapma bildirimleri.
            </p>
            <span className={styles.moduleAction}>Modülü Aç →</span>
          </Link>
        </div>
      </section>
    </>
  );
}
