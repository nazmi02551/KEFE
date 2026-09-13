'use client';

import React, { useEffect, useState } from 'react';
import styles from './evidence-builder-workspace.module.css';
import {
  EvidenceBuilderApiClient,
  EvidenceRecord,
  EvidenceCategory,
} from '../lib/evidence-builder-api';

export function EvidenceBuilderWorkspace() {
  const [evidenceList, setEvidenceList] = useState<EvidenceRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [caseVersionId, setCaseVersionId] = useState<string>(
    '123e4567-e89b-12d3-a456-426614174000'
  );

  const [title, setTitle] = useState<string>('');
  const [publisher, setPublisher] = useState<string>('');
  const [category, setCategory] = useState<EvidenceCategory>('ACADEMIC_PEER_REVIEWED');
  const [sourceUrl, setSourceUrl] = useState<string>('');
  const [doiRef, setDoiRef] = useState<string>('');

  const client = new EvidenceBuilderApiClient();

  useEffect(() => {
    loadEvidence(caseVersionId);
  }, [caseVersionId]);

  async function loadEvidence(id: string) {
    setLoading(true);
    try {
      const items = await client.listCaseEvidence(id);
      setEvidenceList(items);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateEvidence(e: React.FormEvent) {
    e.preventDefault();
    if (!title || (!sourceUrl && !doiRef)) return;

    try {
      const created = await client.createEvidence({
        case_version_id: caseVersionId,
        category,
        title,
        publisher: publisher || 'Doğrulanmış Yayıncı',
        source_url: sourceUrl || undefined,
        doi_or_doc_ref: doiRef || undefined,
      });
      setEvidenceList((prev) => [created, ...prev]);
      setTitle('');
      setSourceUrl('');
      setDoiRef('');
    } catch (err) {
      alert((err as Error).message);
    }
  }

  async function handleVerify(evidenceId: string) {
    try {
      const updated = await client.verifyEvidence(
        evidenceId,
        'EXPERT_AUDITED',
        'auditor-admin',
        'Admin Studio üzerinden doğrulandı.'
      );
      setEvidenceList((prev) =>
        prev.map((item) => (item.evidence_id === evidenceId ? updated : item))
      );
    } catch (err) {
      alert((err as Error).message);
    }
  }

  return (
    <div className={styles.shell}>
      <header className={styles.hero}>
        <div>
          <div className={styles.eyebrow}>CAP-098 · Epistemic Rigor</div>
          <h1 className={styles.title}>Kanıt ve Kaynak İnşa Edici (Evidence Builder)</h1>
          <p className={styles.subtitle}>
            İddia ve argümanları somut, doğrulanabilir akademik, resmi ve kurumsal
            kanıt kayıtlarına bağlama ve denetleme masası.
          </p>
        </div>
        <div className={styles.boundaryCard}>
          <strong>Doğrulanabilirlik İlkesi</strong>
          KEFE-EVIDENCE-BUILDER-001 uyarınca her kanıt öğesi geçerli bir URI veya DOI/doküman
          referansı içermek zorundadır. Özetler herkese açık tutulur.
        </div>
      </header>

      <div className={styles.card}>
        <h2 className={styles.cardTitle}>Yeni Kanıt Kaydı Bağla</h2>
        <form onSubmit={handleCreateEvidence}>
          <div className={styles.formGrid}>
            <div className={`${styles.inputGroup} ${styles.fullWidth}`}>
              <label>Kanıt Başlığı / Makale Adı</label>
              <input
                className={styles.input}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Örn: Kamusal Müzakere ve Kutuplaşma Üzerine Ampirik Çalışma"
                required
              />
            </div>
            <div className={styles.inputGroup}>
              <label>Kategori</label>
              <select
                className={styles.select}
                value={category}
                onChange={(e) => setCategory(e.target.value as EvidenceCategory)}
              >
                <option value="ACADEMIC_PEER_REVIEWED">Akademik (Hakemli Dergi)</option>
                <option value="OFFICIAL_GOVERNMENT_STAT">Resmi Devlet İstatistiği</option>
                <option value="INVESTIGATIVE_JOURNALISM">Araştırmacı Gazetecilik</option>
                <option value="INSTITUTIONAL_REPORT">Bağımsız Kurumsal Rapor</option>
              </select>
            </div>
            <div className={styles.inputGroup}>
              <label>Yayıncı / Kurum</label>
              <input
                className={styles.input}
                value={publisher}
                onChange={(e) => setPublisher(e.target.value)}
                placeholder="Örn: TÜİK, Oxford University Press, BM"
              />
            </div>
            <div className={styles.inputGroup}>
              <label>Kaynak URL</label>
              <input
                className={styles.input}
                value={sourceUrl}
                onChange={(e) => setSourceUrl(e.target.value)}
                placeholder="https://..."
              />
            </div>
            <div className={styles.inputGroup}>
              <label>DOI veya Belge Referansı</label>
              <input
                className={styles.input}
                value={doiRef}
                onChange={(e) => setDoiRef(e.target.value)}
                placeholder="10.1000/182 veya Resmi Gazete No: 31400"
              />
            </div>
          </div>
          <button type="submit" className={styles.button}>
            Kanıtı Vakaya Bağla
          </button>
        </form>
      </div>

      <div className={styles.card}>
        <h2 className={styles.cardTitle}>Vakaya Bağlı Kanıtlar</h2>
        {loading ? (
          <div>Yükleniyor...</div>
        ) : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Başlık</th>
                <th>Kategori</th>
                <th>Yayıncı</th>
                <th>Durum</th>
                <th>İşlem</th>
              </tr>
            </thead>
            <tbody>
              {evidenceList.map((item) => (
                <tr key={item.evidence_id}>
                  <td>
                    <strong>{item.title}</strong>
                    {item.source_url ? (
                      <div style={{ fontSize: '0.8rem', color: '#38BDF8' }}>
                        <a href={item.source_url} target="_blank" rel="noreferrer">
                          Kaynak Linki ↗
                        </a>
                      </div>
                    ) : null}
                  </td>
                  <td>{item.category}</td>
                  <td>{item.publisher}</td>
                  <td>
                    <span
                      className={
                        item.verification_status === 'EXPERT_AUDITED' ||
                        item.verification_status === 'COMMUNITY_VERIFIED'
                          ? styles.badgeVerified
                          : styles.badgeUnverified
                      }
                    >
                      {item.verification_status}
                    </span>
                  </td>
                  <td>
                    {item.verification_status === 'UNVERIFIED' ? (
                      <button
                        className={styles.button}
                        style={{ padding: '0.3rem 0.6rem', fontSize: '0.8rem' }}
                        onClick={() => handleVerify(item.evidence_id)}
                      >
                        Doğrula (Audit)
                      </button>
                    ) : (
                      <span style={{ color: '#10B981', fontSize: '0.85rem' }}>Doğrulandı ✓</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
