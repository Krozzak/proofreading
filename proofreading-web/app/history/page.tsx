'use client';

/**
 * History page - shows user's past comparisons.
 * Accessible from the user menu dropdown.
 */

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useAuth } from '@/lib/auth-context';
import { getUserHistory, deleteHistoryEntry } from '@/lib/history-api';
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

  // Redirect if not logged in
  useEffect(() => {
    if (!loading && !user) {
      router.push('/');
    }
  }, [loading, user, router]);

  // Fetch history
  useEffect(() => {
    const fetchHistory = async () => {
      if (!user) return;

      setIsLoading(true);
      setError(null);

      try {
        const token = await getIdToken();
        if (!token) {
          throw new Error('Not authenticated');
        }

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

    if (user) {
      fetchHistory();
    }
  }, [user, getIdToken]);

  const handleDelete = async (fileSignature: string) => {
    if (!confirm('Supprimer cette entrée de l\'historique ?')) return;

    try {
      const token = await getIdToken();
      if (!token) return;

      await deleteHistoryEntry(token, fileSignature);

      // Update local state
      setEntries(entries.filter((e) => e.fileSignature !== fileSignature));
      setTotal(total - 1);
    } catch (err) {
      console.error('Failed to delete entry:', err);
      alert('Erreur lors de la suppression');
    }
  };

  // Filter entries
  const filteredEntries = entries.filter((entry) => {
    // Status filter
    if (filterStatus !== 'all' && entry.validation !== filterStatus) {
      return false;
    }

    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      const filename = entry.originalFile?.name || entry.printerFile?.name || '';
      return (
        entry.code.toLowerCase().includes(query) ||
        filename.toLowerCase().includes(query)
      );
    }

    return true;
  });

  const getValidationBadge = (validation: string) => {
    switch (validation) {
      case 'approved':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
            ✓ Approuvé
          </span>
        );
      case 'rejected':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
            ✗ Rejeté
          </span>
        );
      case 'partial':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
            ◐ Partiel
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            ○ En attente
          </span>
        );
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Loading state
  if (loading || !user) {
    return (
      <main className="min-h-screen flex flex-col">
        <header className="bg-primary text-white py-6 px-8">
          <div className="max-w-6xl mx-auto">
            <div className="w-48 h-8 bg-white/10 animate-pulse rounded" />
          </div>
        </header>
        <div className="flex-1 flex items-center justify-center">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="bg-primary text-white py-6 px-8">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center gap-4">
            <Image
              src="/logo.png"
              alt="ProofsLab Logo"
              width={48}
              height={48}
              className="drop-shadow-lg"
            />
            <div>
              <h1 className="text-2xl font-bold tracking-tight">ProofsLab</h1>
              <p className="text-primary-foreground/80 text-sm">Historique</p>
            </div>
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/dashboard">
              <Button variant="secondary" size="sm">
                Tableau de bord
              </Button>
            </Link>
            <Link href="/">
              <Button variant="secondary" size="sm">
                Retour
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 max-w-6xl mx-auto w-full px-8 py-8">
        <Card className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold">Historique des comparaisons</h2>
              <p className="text-sm text-muted-foreground">
                {total} entrée{total > 1 ? 's' : ''} dans l&apos;historique
              </p>
            </div>

            {/* Filters */}
            <div className="flex items-center gap-3">
              {/* Search */}
              <div className="relative">
                <input
                  type="text"
                  placeholder="Rechercher..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8 pr-8 py-2 text-sm border rounded-md w-48 focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
                <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground">
                  🔎
                </span>
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  >
                    ✕
                  </button>
                )}
              </div>

              {/* Status filter */}
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50"
              >
                <option value="all">Tous les statuts</option>
                <option value="approved">Approuvés</option>
                <option value="rejected">Rejetés</option>
                <option value="partial">Partiels</option>
                <option value="pending">En attente</option>
              </select>
            </div>
          </div>

          {/* Error state */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center mb-4">
              <p className="text-red-700">{error}</p>
            </div>
          )}

          {/* Loading state */}
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
            </div>
          )}

          {/* Empty state */}
          {!isLoading && entries.length === 0 && (
            <div className="text-center py-12">
              <p className="text-muted-foreground mb-4">
                Aucune comparaison dans l&apos;historique
              </p>
              <Link href="/">
                <Button>Commencer une comparaison</Button>
              </Link>
            </div>
          )}

          {/* Table */}
          {!isLoading && filteredEntries.length > 0 && (
            <div className="border rounded-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-24">Code</TableHead>
                    <TableHead>Fichier</TableHead>
                    <TableHead className="w-24 text-center">Similarité</TableHead>
                    <TableHead className="w-28 text-center">Statut</TableHead>
                    <TableHead className="w-40">Date</TableHead>
                    <TableHead className="w-20 text-center">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredEntries.map((entry) => (
                    <TableRow key={entry.id}>
                      <TableCell className="font-mono font-medium">
                        {entry.code}
                      </TableCell>
                      <TableCell className="truncate max-w-[250px]">
                        {entry.originalFile?.name || entry.printerFile?.name || '-'}
                      </TableCell>
                      <TableCell className="text-center">
                        {entry.similarity !== null ? (
                          <span
                            className={
                              entry.similarity >= 85
                                ? 'text-green-600 font-medium'
                                : 'text-red-600 font-medium'
                            }
                          >
                            {Math.round(entry.similarity)}%
                          </span>
                        ) : (
                          <span className="text-muted-foreground">N/A</span>
                        )}
                      </TableCell>
                      <TableCell className="text-center">
                        {getValidationBadge(entry.validation)}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatDate(entry.updatedAt)}
                      </TableCell>
                      <TableCell className="text-center">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(entry.fileSignature)}
                          className="text-red-500 hover:text-red-700 hover:bg-red-50"
                        >
                          Supprimer
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}

          {/* No results for filter */}
          {!isLoading && entries.length > 0 && filteredEntries.length === 0 && (
            <div className="text-center py-8">
              <p className="text-muted-foreground">
                Aucun résultat pour ces filtres
              </p>
            </div>
          )}
        </Card>
      </div>

      {/* Footer */}
      <footer className="py-4 text-center text-sm text-muted-foreground border-t">
        <p>ProofsLab v1.2.0 - PDF Comparison Laboratory</p>
      </footer>
    </main>
  );
}
