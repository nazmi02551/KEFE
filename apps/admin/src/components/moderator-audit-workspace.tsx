'use client';

import React, { useEffect, useState } from 'react';
import styles from './moderator-audit-workspace.module.css';
import {
  ModeratorAuditApiClient,
  ModeratorAuditEntry,
  ModerationActionType,
} from '../lib/moderator-audit-api';

export function ModeratorAuditWorkspace() {
  const [logs, setLogs] = useState<ModeratorAuditEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionFilter, setActionFilter] = useState<string>('');

  const client = new ModeratorAuditApiClient();

  useEffect(() => {
    async function loadLogs() {
      setLoading(true);
      try {
        const items = await client.listAuditLogs(
          actionFilter ? (actionFilter as ModerationActionType) : undefined
        );
        setLogs(items);
      } finally {
        setLoading(false);
      }
    }
    loadLogs();
  }, [actionFilter]);

  return (
    <div className={styles.shell}>
      <header className={styles.hero}>
        <div>
          <div className={styles.eyebrow}>CAP-067 · Governance & Transparency</div>
          <h1 className={styles.title}>Moderatör Eylem Denetim Zinciri (Audit Log)</h1>
          <p className={styles.subtitle}>
            Platform üzerindeki tüm silme, dondurma, uyarı ve itiraz kararlarının
            kriptografik SHA-256 zinciriyle şeffaf şekilde kaydedildiği kamu denetim masası.
          </p>
        </div>
        <div className={styles.boundaryCard}>
          <strong>Geri Alınamaz Kriptografik Kayıt</strong>
          KEFE-MOD-AUDIT-001 gereğince her karar bir anayasal politika kuralına
          bağlanmak ve değiştirilemez bir hash ile zincire eklenmek zorundadır.
        </div>
      </header>

      <div className={styles.card}>
        <div className={styles.filterRow}>
          <select
            className={styles.select}
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
          >
            <option value="">Tüm Eylem Tipleri</option>
            <option value="REASON_REMOVED_POLICY_BREACH">Gerekçe Kaldırma (İhlal)</option>
            <option value="FLAG_DISMISSED_VALID">İtiraz Reddi (İçerik Geçerli)</option>
            <option value="CASE_VERSION_FREEZE">Vaka Sürümü Dondurma</option>
            <option value="USER_WARNING_ISSUED">Kullanıcı Uyarısı</option>
          </select>
        </div>

        {loading ? (
          <div>Denetim zinciri yükleniyor...</div>
        ) : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Denetim ID</th>
                <th>Eylem Tipi</th>
                <th>Moderatör</th>
                <th>Politika Referansı</th>
                <th>Gerekçe / Açıklama</th>
                <th>Kriptografik Hash</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((entry) => (
                <tr key={entry.audit_id}>
                  <td>
                    <strong>{entry.audit_id}</strong>
                  </td>
                  <td>
                    <span
                      className={`${styles.badge} ${
                        entry.action_type === 'REASON_REMOVED_POLICY_BREACH'
                          ? styles.badgePolicy
                          : entry.action_type === 'FLAG_DISMISSED_VALID'
                          ? styles.badgeDismiss
                          : styles.badgeFreeze
                      }`}
                    >
                      {entry.action_type}
                    </span>
                  </td>
                  <td>{entry.moderator_id}</td>
                  <td>{entry.policy_rule_reference}</td>
                  <td>{entry.justification_text}</td>
                  <td>
                    <span className={styles.hashText} title={entry.action_hash}>
                      {entry.action_hash.slice(0, 16)}...
                    </span>
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
