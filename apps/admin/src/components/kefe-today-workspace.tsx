'use client';

import React, { useEffect, useState } from 'react';
import styles from './kefe-today-workspace.module.css';
import { KefeTodayApiClient, TodayCaseData } from '../lib/kefe-today-api';

export function KefeTodayWorkspace() {
  const [todayCase, setTodayCase] = useState<TodayCaseData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const [caseId, setCaseId] = useState<string>('case-real-event-2026-09');
  const [caseVersionId, setCaseVersionId] = useState<string>(
    '22222222-2222-4222-8222-222222222222'
  );
  const [title, setTitle] = useState<string>('');
  const [summary, setSummary] = useState<string>('');
  const [headline, setHeadline] = useState<string>('');
  const [domain, setDomain] = useState<string>('Technology');

  const client = new KefeTodayApiClient();

  useEffect(() => {
    loadToday();
  }, []);

  async function loadToday() {
    setLoading(true);
    try {
      const data = await client.getTodayCase();
      setTodayCase(data);
    } finally {
      setLoading(false);
    }
  }

  async function handleCurate(e: React.FormEvent) {
    e.preventDefault();
    if (!title || !summary || !headline) return;

    try {
      const updated = await client.curateTodayCase({
        case_id: caseId,
        case_version_id: caseVersionId,
        title,
        summary,
        editorial_headline: headline,
        is_real_event: true,
        domain,
      });
      setTodayCase(updated);
      alert('Günün vakası başarıyla vitrine yerleştirildi.');
    } catch (err) {
      alert((err as Error).message);
    }
  }

  return (
    <div className={styles.shell}>
      <header className={styles.hero}>
        <div>
          <div className={styles.eyebrow}>CAP-026 · Editorial Curation</div>
          <h1 className={styles.title}>KEFE Today & Sıcak Olay Projeksiyonu</h1>
          <p className={styles.subtitle}>
            Gerçek dünyada yaşanan somut ikilemlerin editoryal olarak kürate edilip
            tüketici ana ekran vitrinine (KEFE Today) yansıtılması masası.
          </p>
        </div>
        <div className={styles.boundaryCard}>
          <strong>Gerçek Olay Güvencesi</strong>
          KEFE-TODAY-REAL-EVENT-PROJECTION-001 uyarınca yalnızca doğrulanmış
          is_real_event = true nitelikli vakalar vitrine seçilebilir.
        </div>
      </header>

      {loading && !todayCase ? (
        <div>Yükleniyor...</div>
      ) : todayCase ? (
        <div className={styles.card}>
          <h2 className={styles.cardTitle}>Yayındaki Günün Vakası Vitrini</h2>
          <div className={styles.headlineBox}>
            <span className={styles.badgeRealEvent}>GERÇEK OLAY · IS_REAL_EVENT</span>
            <div className={styles.headline}>{todayCase.editorial_headline}</div>
            <div className={styles.caseTitle}>{todayCase.title} ({todayCase.domain})</div>
            <p className={styles.caseSummary}>{todayCase.summary}</p>
          </div>
        </div>
      ) : null}

      <div className={styles.card}>
        <h2 className={styles.cardTitle}>Yeni Bir Günün Vakasını Vitrine Al</h2>
        <form onSubmit={handleCurate}>
          <div className={styles.formGrid}>
            <div className={styles.inputGroup}>
              <label>Vaka ID</label>
              <input
                className={styles.input}
                value={caseId}
                onChange={(e) => setCaseId(e.target.value)}
                required
              />
            </div>
            <div className={styles.inputGroup}>
              <label>Vaka Sürüm UUID</label>
              <input
                className={styles.input}
                value={caseVersionId}
                onChange={(e) => setCaseVersionId(e.target.value)}
                required
              />
            </div>
            <div className={`${styles.inputGroup} ${styles.fullWidth}`}>
              <label>Editoryal Manşet (Headline)</label>
              <input
                className={styles.input}
                value={headline}
                onChange={(e) => setHeadline(e.target.value)}
                placeholder="Örn: Günün Sıcak İkilemi: Otonom Araçlarda Yasal Sorumluluk"
                required
              />
            </div>
            <div className={`${styles.inputGroup} ${styles.fullWidth}`}>
              <label>Vaka Başlığı</label>
              <input
                className={styles.input}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Örn: Otonom Trafik ve Acil Durum Manevraları"
                required
              />
            </div>
            <div className={`${styles.inputGroup} ${styles.fullWidth}`}>
              <label>Özet / Bağlam Açıklaması</label>
              <textarea
                className={styles.textarea}
                value={summary}
                onChange={(e) => setSummary(e.target.value)}
                placeholder="Olayın arka planını ve karşı karşıya gelen temel ilkeleri özetleyin..."
                required
              />
            </div>
          </div>
          <button type="submit" className={styles.button}>
            Günün Vakasını Yayınla (Curate)
          </button>
        </form>
      </div>
    </div>
  );
}
