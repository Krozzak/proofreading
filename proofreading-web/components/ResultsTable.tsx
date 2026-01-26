'use client';

import { useMemo } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { ComparisonPair } from '@/lib/types';

interface ResultsTableProps {
  pairs: ComparisonPair[];
  currentIndex: number;
  onSelectPair: (index: number) => void;
  onExportCSV: () => void;
  onCopyClipboard: () => void;
  showMatchedOnly: boolean;
  onToggleFilter: () => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  onCalculateAll?: () => void;
  isBatchCalculating?: boolean;
  batchProgress?: { current: number; total: number };
  onAutoApprove?: () => void;
  threshold?: number;
  restoredIndices?: Set<number>;
}

export function ResultsTable({
  pairs,
  currentIndex,
  onSelectPair,
  onExportCSV,
  onCopyClipboard,
  showMatchedOnly,
  onToggleFilter,
  searchQuery,
  onSearchChange,
  onCalculateAll,
  isBatchCalculating,
  batchProgress,
  onAutoApprove,
  threshold,
  restoredIndices,
}: ResultsTableProps) {
  const filteredPairs = useMemo(() => {
    let result = showMatchedOnly
      ? pairs.filter((p) => p.originalFile && p.printerFile)
      : pairs;

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim();
      result = result.filter(
        (p) =>
          p.code.toLowerCase().includes(query) ||
          p.originalFile?.name.toLowerCase().includes(query) ||
          p.printerFile?.name.toLowerCase().includes(query)
      );
    }

    return result;
  }, [pairs, showMatchedOnly, searchQuery]);

  const getMatchingStatus = (pair: ComparisonPair) => {
    if (pair.originalFile && pair.printerFile) return 'Les deux';
    if (pair.originalFile) return 'Original seul';
    return 'Imprimeur seul';
  };

  const getValidationBadge = (pair: ComparisonPair) => {
    switch (pair.validation) {
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

  return (
    <div className="space-y-4">
      {/* Actions bar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={onToggleFilter}
          >
            {showMatchedOnly ? 'Tous les fichiers' : 'Correspondants'}
          </Button>
          <span className="text-sm text-muted-foreground">
            {filteredPairs.length} fichier{filteredPairs.length > 1 ? 's' : ''}
          </span>

          {/* Search input */}
          <div className="relative ml-2">
            <input
              type="text"
              placeholder="Rechercher..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-7 pr-7 py-1.5 text-sm border rounded-md w-40 focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <span className="absolute left-2 top-1/2 -translate-y-1/2 text-muted-foreground text-xs">
              🔎
            </span>
            {searchQuery && (
              <button
                onClick={() => onSearchChange('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground text-xs"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {onCalculateAll && (
            <Button
              variant="outline"
              size="sm"
              onClick={onCalculateAll}
              disabled={isBatchCalculating}
            >
              {isBatchCalculating ? (
                <>
                  <span className="animate-spin mr-1">⏳</span>
                  {batchProgress?.current}/{batchProgress?.total}
                </>
              ) : (
                'Tout calculer'
              )}
            </Button>
          )}
          {onAutoApprove && (
            <Button
              variant="outline"
              size="sm"
              onClick={onAutoApprove}
              className="text-green-600 border-green-600 hover:bg-green-50"
            >
              Auto-approuver ({'>='}{threshold}%)
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={onExportCSV}>
            CSV
          </Button>
          <Button variant="outline" size="sm" onClick={onCopyClipboard}>
            Copier
          </Button>
        </div>
      </div>

      {/* Table */}
      <div className="border rounded-lg overflow-hidden max-h-[300px] overflow-y-auto">
        <Table>
          <TableHeader className="sticky top-0 bg-muted">
            <TableRow>
              <TableHead className="w-24">Code</TableHead>
              <TableHead>Fichier</TableHead>
              <TableHead className="w-28">Matching</TableHead>
              <TableHead className="w-24 text-center">Similarité</TableHead>
              <TableHead className="w-28 text-center">Statut</TableHead>
              <TableHead className="w-20 text-center">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredPairs.map((pair, idx) => {
              const displayIndex = pairs.indexOf(pair);
              const isSelected = displayIndex === currentIndex;

              return (
                <TableRow
                  key={pair.index}
                  className={cn(
                    'cursor-pointer transition-colors',
                    isSelected && 'bg-primary/10',
                    pair.validation === 'approved' && 'bg-green-50',
                    pair.validation === 'rejected' && 'bg-red-50'
                  )}
                  onClick={() => onSelectPair(displayIndex)}
                >
                  <TableCell className="font-mono font-medium">
                    <span className="flex items-center gap-1">
                      {pair.code}
                      {restoredIndices?.has(displayIndex) && (
                        <span
                          className="text-blue-500 cursor-help"
                          title="Restauré de l'historique"
                        >
                          🕐
                        </span>
                      )}
                    </span>
                  </TableCell>
                  <TableCell className="truncate max-w-[200px]">
                    {pair.originalFile?.name || pair.printerFile?.name || '-'}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {getMatchingStatus(pair)}
                  </TableCell>
                  <TableCell className="text-center">
                    {pair.similarity !== null ? (
                      <span
                        className={cn(
                          'font-medium',
                          pair.similarity >= 85
                            ? 'text-green-600'
                            : 'text-red-600'
                        )}
                      >
                        {Math.round(pair.similarity)}%
                      </span>
                    ) : (
                      <span className="text-muted-foreground">N/A</span>
                    )}
                  </TableCell>
                  <TableCell className="text-center">
                    {getValidationBadge(pair)}
                  </TableCell>
                  <TableCell className="text-center">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectPair(displayIndex);
                      }}
                    >
                      Voir
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
