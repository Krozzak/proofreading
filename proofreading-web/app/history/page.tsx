'use client';

/**
 * History page - shows user's past comparisons.
 * Accessible from the user menu dropdown.
 */

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { getUserHistory, deleteHistoryEntry } from '@/lib/history-api';
import { NavBar } from '@/components/NavBar';
import { SiteFooter } from '@/components/SiteFooter';
import type { HistoryEntry } from '@/lib/types';

export default function HistoryPage() {
  const router = useRouter();
  const { user, loading, getIdToken } = useAuth();

  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');

  useEffect(() => {
    if (!loading && !user) router.push('/');
  }, [loading, user, router]);

  useEffect(() => {
    const fetchHistory = async () => {
      if (!user) return;
      setIsLoading(true);
      setError(null);
      try {
        const token = await getIdToken();
        if (!token) throw new Error('Not authenticated');
        const result = await getUserHistory(token, 100, 0);
        setEntries(result.entries);
        setTotal(result.total);
      } catch (err) {
        console.error('Failed to fetch history:', err);
        setError('Impossible de charger l\'historique');
      } finally {
        setIsLoading(false);
      }
    };
    if (user) fetchHistory();
  }, [user, getIdToken]);

  const handleDelete = async (fileSignature: string) => {
    if (!confirm('Supprimer cette entrée de l\'historique ?')) return;
    try {
      const token = await getIdToken();
      if (!token) return;
      await deleteHistoryEntry(token, fileSignature);
      setEntries(entries.filter(e => e.fileSignature !== fileSignature));
      setTotal(total - 1);
    } catch (err) {
      console.error('Failed to delete entry:', err);
      alert('Erreur lors de la suppression');
    }
  };

  const filteredEntries = entries.filter(entry => {
    if (filterStatus !== 'all' && entry.validation !== filterStatus) return false;
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      const filename = entry.originalFile?.name || entry.printerFile?.name || '';
      return entry.code.toLowerCase().includes(query) || filename.toLowerCase().includes(query);
    }
    return true;
  });

  const getValidationBadge = (validation: string) => {
    const badges: Record<string, { label: string; bg: string; color: string; icon: React.ReactNode }> = {
      approved: {
        label: 'Approuvé',
        bg: 'color-mix(in oklab, var(--c3) 20%, transparent)',
        color: '#0a4d32',
        icon: <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6L9 17l-5-5"/></svg>,
      },
      rejected: {
        label: 'Rejeté',
        bg: 'color-mix(in oklab, var(--c1) 15%, transparent)',
        color: '#8b1a14',
        icon: <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6L6 18M6 6l12 12"/></svg>,
      },
      partial: {
        label: 'Partiel',
        bg: 'color-mix(in oklab, var(--c2) 25%, transparent)',
        color: '#5c3d00',
        icon: <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a10 10 0 0 1 0 20"/></svg>,
      },
    };
    const b = badges[validation] ?? {
      label: 'En attente',
      bg: 'var(--muted)',
      color: 'var(--muted-foreground)',
      icon: <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="9"/></svg>,
    };
    return (
      <span style={{
        display: 'inline-flex', alignItems: 'center', gap: 5,
        padding: '3px 10px', borderRadius: 999, fontSize: 12, fontWeight: 600,
        background: b.bg, color: b.color,
      }}>
        {b.icon}
        {b.label}
      </span>
    );
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '—';
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: 'numeric', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  };

  if (loading || !user) {
    return (
      <main style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--background)' }}>
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ width: 32, height: 32, border: '3px solid var(--border)', borderTop: '3px solid var(--accent)', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
        </div>
      </main>
    );
  }

  return (
    <main style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--background)' }}>

      {/* ── Header ── */}
      <NavBar />

      {/* ── Main ── */}
      <div className="history-main" style={{ flex: 1, maxWidth: 1100, margin: '0 auto', width: '100%', padding: '48px 32px' }}>

        {/* Title + Toolbar inline */}
        <div style={{
          display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between',
          gap: 24, flexWrap: 'wrap', marginBottom: 32,
        }}>
          {/* Left: title */}
          <div>
            <div style={{ fontSize: 12, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--muted-foreground)', marginBottom: 12 }}>
              Historique
            </div>
            <h1 style={{ fontSize: 'clamp(40px, 5vw, 64px)', margin: 0, lineHeight: 1, letterSpacing: '-0.03em', fontWeight: 500 }}>
              Comparaisons{' '}
              <em style={{ fontFamily: 'var(--font-instrument-serif)', fontStyle: 'italic', fontWeight: 400, color: 'var(--c4)' }}>
                récentes.
              </em>
            </h1>
          </div>

          {/* Right: toolbar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', flexShrink: 0 }}>
            {/* Search */}
            <div style={{ position: 'relative' }}>
              <span style={{
                position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)',
                display: 'flex', color: 'var(--muted-foreground)', pointerEvents: 'none',
              }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35"/>
                </svg>
              </span>
              <input
                type="text"
                placeholder="Rechercher…"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                style={{
                  paddingLeft: 32, paddingRight: searchQuery ? 28 : 12,
                  paddingTop: 8, paddingBottom: 8,
                  fontSize: 13, border: '1px solid var(--border)',
                  borderRadius: 10, width: 180, outline: 'none',
                  background: 'var(--muted)', color: 'var(--foreground)',
                }}
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  style={{
                    position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)',
                    background: 'none', border: 'none', cursor: 'pointer',
                    color: 'var(--muted-foreground)', display: 'flex', alignItems: 'center',
                  }}
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M18 6L6 18M6 6l12 12"/>
                  </svg>
                </button>
              )}
            </div>

            {/* Status filter */}
            <select
              value={filterStatus}
              onChange={e => setFilterStatus(e.target.value)}
              style={{
                padding: '8px 12px', fontSize: 13,
                border: '1px solid var(--border)', borderRadius: 10,
                background: 'var(--muted)', color: 'var(--foreground)', outline: 'none',
              }}
            >
              <option value="all">Tous les statuts</option>
              <option value="approved">Approuvés</option>
              <option value="rejected">Rejetés</option>
              <option value="partial">Partiels</option>
              <option value="pending">En attente</option>
            </select>

            {/* Export CSV — à implémenter (roadmap) */}
            <button
              disabled
              title="Export CSV — fonctionnalité à venir"
              style={{
                padding: '8px 14px', fontSize: 13, fontWeight: 500,
                background: 'var(--muted)', color: 'var(--muted-foreground)',
                border: '1px solid var(--border)', borderRadius: 10,
                cursor: 'not-allowed', display: 'flex', alignItems: 'center', gap: 7,
                opacity: 0.5,
              }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5 5 5-5M12 15V3"/>
              </svg>
              Export
            </button>
          </div>
        </div>

        {/* Stat cards */}
        <div className="history-stat-cards" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 32 }}>
          {[
            { label: 'Total', value: total, color: 'var(--foreground)' },
            { label: 'Approuvés', value: entries.filter(e => e.validation === 'approved').length, color: 'var(--c3)' },
            { label: 'Rejetés', value: entries.filter(e => e.validation === 'rejected').length, color: 'var(--c1)' },
            { label: 'Temps moyen', value: '—', color: 'var(--c4)' /* TODO: calculer depuis l'API */ },
          ].map(s => (
            <div key={s.label} style={{
              background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 16, padding: 20,
            }}>
              <div style={{ fontSize: 11, color: 'var(--muted-foreground)', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 8 }}>
                {s.label}
              </div>
              <div style={{
                fontSize: 40, fontWeight: 500, color: s.color,
                letterSpacing: '-0.03em', lineHeight: 1,
                fontFamily: 'var(--font-geist-mono)',
              }}>
                {s.value}
              </div>
            </div>
          ))}
        </div>

        {/* Card */}
        <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 24, overflow: 'hidden' }}>

          {/* Error */}
          {error && (
            <div style={{ padding: '16px 24px', background: 'color-mix(in oklab, var(--destructive) 8%, var(--background))', borderBottom: '1px solid color-mix(in oklab, var(--destructive) 20%, transparent)' }}>
              <p style={{ color: 'var(--destructive)', margin: 0, fontSize: 14 }}>{error}</p>
            </div>
          )}

          {/* Loading */}
          {isLoading && (
            <div style={{ padding: 64, display: 'flex', justifyContent: 'center' }}>
              <div style={{ width: 32, height: 32, border: '3px solid var(--border)', borderTop: '3px solid var(--c4)', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
            </div>
          )}

          {/* Empty state */}
          {!isLoading && entries.length === 0 && (
            <div style={{ padding: 64, textAlign: 'center' }}>
              <p style={{ fontSize: 48, marginBottom: 16 }}>📂</p>
              <p style={{ color: 'var(--muted-foreground)', marginBottom: 20 }}>
                Aucune comparaison dans l&apos;historique
              </p>
              <Link href="/">
                <button style={{
                  padding: '10px 22px', fontSize: 14, fontWeight: 600,
                  background: 'var(--c4)', color: '#fff',
                  border: 'none', borderRadius: 12, cursor: 'pointer',
                }}>
                  Commencer une comparaison
                </button>
              </Link>
            </div>
          )}

          {/* Table */}
          {!isLoading && filteredEntries.length > 0 && (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    {['Code', 'Fichier', 'Similarité', 'Statut', 'Date', 'Action'].map((h, i) => (
                      <th key={h} style={{
                        padding: '12px 16px',
                        fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase',
                        color: 'var(--muted-foreground)', textAlign: i >= 2 ? 'center' : 'left',
                        whiteSpace: 'nowrap',
                      }}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredEntries.map((entry, idx) => (
                    <tr
                      key={entry.id}
                      style={{
                        borderBottom: idx < filteredEntries.length - 1 ? '1px solid var(--border)' : 'none',
                        transition: 'background .1s',
                      }}
                      onMouseEnter={e => (e.currentTarget.style.background = 'var(--muted)')}
                      onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                    >
                      <td style={{ padding: '12px 16px', fontFamily: 'var(--font-geist-mono)', fontSize: 13, fontWeight: 700 }}>
                        {entry.code}
                      </td>
                      <td style={{ padding: '12px 16px', fontSize: 13, maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {entry.originalFile?.name || entry.printerFile?.name || '—'}
                      </td>
                      <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                        {entry.similarity !== null ? (
                          <span style={{
                            fontFamily: 'var(--font-geist-mono)', fontSize: 13, fontWeight: 700,
                            color: entry.similarity >= 85 ? 'var(--c3)' : 'var(--c1)',
                          }}>
                            {Math.round(entry.similarity)}%
                          </span>
                        ) : (
                          <span style={{ color: 'var(--muted-foreground)', fontSize: 13 }}>N/A</span>
                        )}
                      </td>
                      <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                        {getValidationBadge(entry.validation)}
                      </td>
                      <td style={{ padding: '12px 16px', fontSize: 12, color: 'var(--muted-foreground)', whiteSpace: 'nowrap' }}>
                        {formatDate(entry.updatedAt)}
                      </td>
                      <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                        <div style={{ display: 'flex', gap: 6, justifyContent: 'center' }}>
                          {/* Voir — fonctionnalité à venir (roadmap) */}
                          <button
                            disabled
                            title="Voir cette comparaison — fonctionnalité à venir"
                            style={{
                              padding: '5px 10px', fontSize: 12,
                              background: 'transparent', color: 'var(--muted-foreground)',
                              border: '1px solid var(--border)',
                              borderRadius: 8, cursor: 'not-allowed', opacity: 0.4,
                              display: 'flex', alignItems: 'center',
                            }}
                          >
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                            </svg>
                          </button>
                          <button
                            onClick={() => handleDelete(entry.fileSignature)}
                            title="Supprimer cette entrée"
                            style={{
                              padding: '5px 12px', fontSize: 12, fontWeight: 500,
                              background: 'transparent',
                              color: 'var(--destructive)',
                              border: '1px solid color-mix(in oklab, var(--destructive) 40%, transparent)',
                              borderRadius: 8, cursor: 'pointer', transition: 'all .12s',
                            }}
                            onMouseEnter={e => { (e.target as HTMLElement).style.background = 'color-mix(in oklab, var(--destructive) 8%, transparent)'; }}
                            onMouseLeave={e => { (e.target as HTMLElement).style.background = 'transparent'; }}
                          >
                            Supprimer
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* No results */}
          {!isLoading && entries.length > 0 && filteredEntries.length === 0 && (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--muted-foreground)', fontSize: 14 }}>
              Aucun résultat pour ces filtres
            </div>
          )}
        </div>
      </div>

      <SiteFooter />

      <style>{`
        @media (max-width: 640px) {
          .history-main { padding: 32px 20px !important; }
          .history-stat-cards { grid-template-columns: 1fr 1fr !important; }
        }
      `}</style>
    </main>
  );
}
