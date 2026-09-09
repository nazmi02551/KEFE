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
        </div>
      </section>
    </>
  );
}
