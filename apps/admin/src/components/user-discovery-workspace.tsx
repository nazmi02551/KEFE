'use client';

import React, { useEffect, useState } from 'react';
import styles from './user-discovery-workspace.module.css';
import {
  UserDiscoveryApiClient,
  UserDiscoveryProfileData,
  ComplexityLevel,
  FreshnessPreference,
  RealEventPreference,
  DomainPreference,
} from '../lib/user-discovery-api';

export function UserDiscoveryWorkspace() {
  const [profile, setProfile] = useState<UserDiscoveryProfileData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [userId, setUserId] = useState<string>('actor-default-preview');

  const [complexity, setComplexity] = useState<ComplexityLevel>('BALANCED');
  const [freshness, setFreshness] = useState<FreshnessPreference>('BALANCED');
  const [realEvent, setRealEvent] = useState<RealEventPreference>('BALANCED');
  const [boost, setBoost] = useState<number>(0.5);

  const client = new UserDiscoveryApiClient();

  useEffect(() => {
    loadProfile(userId);
  }, [userId]);

  async function loadProfile(id: string) {
    setLoading(true);
    try {
      const p = await client.getProfile(id);
      setProfile(p);
      setComplexity(p.complexity_level);
      setFreshness(p.freshness_preference);
      setRealEvent(p.real_event_preference);
      setBoost(p.diversification_boost);
    } finally {
      setLoading(false);
    }
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    try {
      const updated = await client.updateProfile(userId, {
        preferred_domains: profile?.preferred_domains || ['CIVIC', 'TECHNOLOGY'],
        complexity_level: complexity,
        freshness_preference: freshness,
        real_event_preference: realEvent,
        diversification_boost: boost,
      });
      setProfile(updated);
      alert('Keşif profili başarıyla kaydedildi.');
    } catch (err) {
      alert((err as Error).message);
    }
  }

  return (
    <div className={styles.shell}>
      <header className={styles.hero}>
        <div>
          <div className={styles.eyebrow}>CAP-077 · User Agency</div>
          <h1 className={styles.title}>Kullanıcı Kontrollü Keşif Profili (User Discovery)</h1>
          <p className={styles.subtitle}>
            Algoritmik etkileşim maksimizasyonu ve gözetim yerine vatandaşın
            kendi müzakere akışını ve perspektif çeşitliliğini doğrudan belirlemesi.
          </p>
        </div>
        <div className={styles.boundaryCard}>
          <strong>Gözetimsiz Keşif İlkesi</strong>
          KEFE-USER-DISCOVERY-001 gereğince akışlar asla dopamin, öfke veya ekranda
          kalma süresine (time-on-app) göre optimize edilemez.
        </div>
      </header>

      {loading && !profile ? (
        <div>Profil yükleniyor...</div>
      ) : (
        <>
          <div className={styles.card}>
            <h2 className={styles.cardTitle}>Keşif ve Çeşitlilik Parametreleri</h2>
            <form onSubmit={handleSave}>
              <div className={styles.formGrid}>
                <div className={styles.inputGroup}>
                  <label>Karmaşıklık Düzeyi (Complexity)</label>
                  <select
                    className={styles.select}
                    value={complexity}
                    onChange={(e) => setComplexity(e.target.value as ComplexityLevel)}
                  >
                    <option value="INTRODUCTORY">Giriş Seviyesi (Introductory)</option>
                    <option value="BALANCED">Dengeli (Balanced)</option>
                    <option value="DEEP_DELIBERATION">Derin Müzakere (Deep Deliberation)</option>
                  </select>
                </div>
                <div className={styles.inputGroup}>
                  <label>Güncellik Tercihi (Freshness)</label>
                  <select
                    className={styles.select}
                    value={freshness}
                    onChange={(e) => setFreshness(e.target.value as FreshnessPreference)}
                  >
                    <option value="CURRENT_EVENTS">Sıcak Gündem Olayları</option>
                    <option value="BALANCED">Dengeli Karışım</option>
                    <option value="TIMELESS_FOUNDATIONS">Zamansız Temel İlkeler</option>
                  </select>
                </div>
                <div className={styles.inputGroup}>
                  <label>Gerçek Olay Önceliği (Real Events)</label>
                  <select
                    className={styles.select}
                    value={realEvent}
                    onChange={(e) => setRealEvent(e.target.value as RealEventPreference)}
                  >
                    <option value="REAL_EVENTS_FIRST">Önce Gerçek Olaylar</option>
                    <option value="BALANCED">Dengeli</option>
                    <option value="HYPOTHETICALS_FIRST">Önce Varsayımsal İkilemler</option>
                  </select>
                </div>
                <div className={styles.inputGroup}>
                  <label>Çeşitlilik Güçlendirmesi (Diversification Boost): %{(boost * 100).toFixed(0)}</label>
                  <input
                    type="range"
                    min="0.0"
                    max="1.0"
                    step="0.05"
                    value={boost}
                    onChange={(e) => setBoost(parseFloat(e.target.value))}
                  />
                </div>
              </div>
              <button type="submit" className={styles.button}>
                Keşif Profilini Güncelle
              </button>
            </form>
          </div>

          <div className={styles.card}>
            <h2 className={styles.cardTitle}>Anayasal Keşif Değişmezleri</h2>
            <ul className={styles.invariantsList}>
              <li className={styles.invariantItem}>
                <strong>NO_ENGAGEMENT_MAXIMIZATION:</strong> Keşif akışı bağımlılık ve öfke üretmez.
              </li>
              <li className={styles.invariantItem}>
                <strong>EXPLICIT_USER_AGENCY:</strong> Vaka görünürlük ağırlıkları yalnızca kullanıcının tercihlerine tabidir.
              </li>
              <li className={styles.invariantItem}>
                <strong>SURVEILLANCE_FREE:</strong> Davranışsal profil üçüncü taraflara aktarılmaz veya paraya dönüştürülemez.
              </li>
            </ul>
          </div>
        </>
      )}
    </div>
  );
}
