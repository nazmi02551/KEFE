'use client';

import React, { useEffect, useState } from 'react';
import styles from './source-diversity-workspace.module.css';
import {
  SourceDiversityApiClient,
  SourceDiversityData,
  SourceCategory,
} from '../lib/source-diversity-api';

export function SourceDiversityWorkspace() {
  const [data, setData] = useState<SourceDiversityData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [caseVersionId, setCaseVersionId] = useState<string>(
    '123e4567-e89b-12d3-a456-426614174000'
  );

  const client = new SourceDiversityApiClient();

  useEffect(() => {
    loadDiversity(caseVersionId);
  }, [caseVersionId]);

  async function loadDiversity(id: string) {
    setLoading(true);
    try {
      const res = await client.getSourceDiversity(id);
      setData(res);
    } finally {
      setLoading(false);
    }
  }

  async function addPluralisticSet() {
    setLoading(true);
    try {
      const sampleCategories: SourceCategory[] = [
        'ACADEMIC_SCIENTIFIC',
        'OFFICIAL_GOVERNMENT',
        'CIVIC_INDEPENDENT',
        'MAINSTREAM_JOURNALISM',
        'TECHNICAL_INDUSTRY',
      ];
      const res = await client.evaluateSourceDiversity(caseVersionId, sampleCategories);
      setData(res);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.shell}>
      <header className={styles.hero}>
        <div>
          <div className={styles.eyebrow}>CAP-071 · Trust & Plurality</div>
          <h1 className={styles.title}>Kaynak Çeşitliliği ve Spektrum Denetimi</h1>
          <p className={styles.subtitle}>
            Vakaların tek taraflı editoryal veya siyasi monokültürden beslenmesini önleyen
            kaynak taksonomisi ve çeşitlilik entropisi analizi.
          </p>
        </div>
        <div className={styles.boundaryCard}>
          <strong>Metodolojik Çeşitlilik Standardı</strong>
          KEFE-SOURCE-DIVERSITY-001 gereğince hiçbir vaka tek bir kaynaktan türetilemez.
          Yüksek çeşitlilik en az 3 farklı kategoriyi ve dengeli dağılımı şart koşar.
        </div>
      </header>

      {loading && !data ? (
        <div>Analiz yükleniyor...</div>
      ) : data ? (
        <>
          <div className={styles.statGrid}>
            <div className={styles.statCard}>
              <div className={styles.statLabel}>Toplam Kaynak</div>
              <div className={styles.statValue}>{data.total_sources}</div>
            </div>
            <div className={styles.statCard}>
              <div className={styles.statLabel}>Çeşitlilik Düzeyi</div>
              <div className={styles.statValue}>
                <span
                  className={`${styles.badge} ${
                    data.diversity_level === 'HIGH_DIVERSITY'
                      ? styles.badgeHigh
                      : data.diversity_level === 'BALANCED_DIVERSITY'
                      ? styles.badgeBalanced
                      : styles.badgeLimited
                  }`}
                >
                  {data.diversity_level}
                </span>
              </div>
            </div>
            <div className={styles.statCard}>
              <div className={styles.statLabel}>Farklı Kategori Sayısı</div>
              <div className={styles.statValue}>{data.category_breakdown.length} / 5</div>
            </div>
          </div>

          <div className={styles.card}>
            <h2 className={styles.cardTitle}>Kaynak Kategorileri ve Yüzdesel Dağılım</h2>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Kategori</th>
                  <th>Kaynak Sayısı</th>
                  <th>Oran (%)</th>
                </tr>
              </thead>
              <tbody>
                {data.category_breakdown.map((row) => (
                  <tr key={row.category}>
                    <td>
                      <strong>{row.category}</strong>
                    </td>
                    <td>{row.count}</td>
                    <td>%{row.percentage.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className={styles.formRow}>
              <button className={styles.button} onClick={addPluralisticSet}>
                5 Kategori Pluralist Simülasyonu Çalıştır
              </button>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
