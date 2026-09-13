'use client';

import React, { useEffect, useState } from 'react';
import styles from './open-methodology-workspace.module.css';
import {
  OpenMethodologyApiClient,
  MethodologyDisclosureData,
  MethodologyManifestData,
} from '../lib/open-methodology-api';

export function OpenMethodologyWorkspace() {
  const [disclosure, setDisclosure] = useState<MethodologyDisclosureData | null>(null);
  const [manifest, setManifest] = useState<MethodologyManifestData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const client = new OpenMethodologyApiClient();

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [disc, man] = await Promise.all([
          client.getDisclosure('case', 'demo-case-v1', 180),
          client.getManifestSummary(),
        ]);
        setDisclosure(disc);
        setManifest(man);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className={styles.shell}>
      <header className={styles.hero}>
        <div>
          <div className={styles.eyebrow}>CAP-074 · Transparency & Trust</div>
          <h1 className={styles.title}>Açık Metodoloji ve Hesaplama Şeffaflığı</h1>
          <p className={styles.subtitle}>
            Kolektif konsensüs, sinyal puanlama ve kutuplaşma endeksinin arkasındaki
            matematiksel modeller ve koruma mekanizmaları.
          </p>
        </div>
        <div className={styles.boundaryCard}>
          <strong>Anayasal Şeffaflık İlkesi</strong>
          ADR-0148 uyarınca hiçbir metodoloji ücretli duvarlar arkasına saklanamaz,
          kullanıcılar hakkında psikometrik/siyasi çıkarım yapılamaz (no_psychometric_claims).
        </div>
      </header>

      {loading ? (
        <div>Metodoloji verileri yükleniyor...</div>
      ) : (
        <>
          <div className={styles.statGrid}>
            <div className={styles.statCard}>
              <div className={styles.statLabel}>Metodoloji Motoru</div>
              <div className={styles.statValue}>{disclosure?.engine_version ?? 'v1.0'}</div>
            </div>
            <div className={styles.statCard}>
              <div className={styles.statLabel}>Güvenilirlik Katmanı</div>
              <div className={styles.statValue}>{disclosure?.layer ?? 'TRUSTED'}</div>
            </div>
            <div className={styles.statCard}>
              <div className={styles.statLabel}>Örneklem Boyutu (N)</div>
              <div className={styles.statValue}>{disclosure?.sample_size ?? 0}</div>
            </div>
            <div className={styles.statCard}>
              <div className={styles.statLabel}>Güven Düzeyi</div>
              <div className={styles.statValue}>{disclosure?.confidence ?? 'HIGH'}</div>
            </div>
          </div>

          <div className={styles.card}>
            <h2 className={styles.cardTitle}>Matematiksel Formül ve Hash Kanıtı</h2>
            <div className={styles.formulaBox}>
              <strong>Formül:</strong> {disclosure?.formula_summary}
              <br />
              <strong>Metodoloji SHA-256 Hash:</strong> {disclosure?.methodology_hash}
            </div>
          </div>

          <div className={styles.card}>
            <h2 className={styles.cardTitle}>Anayasal ve Yapısal Koruma Mekanizmaları (Safeguards)</h2>
            <ul className={styles.safeguardsList}>
              {disclosure?.safeguards.map((item) => (
                <li key={item} className={styles.safeguardItem}>
                  <span className={styles.checkIcon}>✓</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          {manifest ? (
            <div className={styles.card}>
              <h2 className={styles.cardTitle}>Motor Formül Manifestosu</h2>
              <div className={styles.formulaBox}>
                {Object.entries(manifest.formula_manifest).map(([k, v]) => (
                  <div key={k} style={{ marginBottom: '0.4rem' }}>
                    <strong>{k}:</strong> {v}
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
