'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { SimilarityBar } from '@/components/SimilarityBar';
import { cn } from '@/lib/utils';
import type { ComparisonPair } from '@/lib/types';

interface ComparisonViewProps {
  pair: ComparisonPair;
  originalPdfUrl: string | null;
  printerPdfUrl: string | null;
  currentPage: number;
  threshold: number;
  onApprove: () => void;
  onReject: (comment: string) => void;
  onPrevPage: () => void;
  onNextPage: () => void;
  onPrevPair: () => void;
  onNextPair: () => void;
  hasPrevPair: boolean;
  hasNextPair: boolean;
  onCalculateSimilarity: () => void;
  isCalculating: boolean;
}

export function ComparisonView({
  pair,
  originalPdfUrl,
  printerPdfUrl,
  currentPage,
  threshold,
  onApprove,
  onReject,
  onPrevPage,
  onNextPage,
  onPrevPair,
  onNextPair,
  hasPrevPair,
  hasNextPair,
  onCalculateSimilarity,
  isCalculating,
}: ComparisonViewProps) {
  const [rejectComment, setRejectComment] = useState('');
  const [showRejectDialog, setShowRejectDialog] = useState(false);

  const maxPages = Math.max(pair.totalPagesOriginal, pair.totalPagesPrinter);
  const hasPrevPage = currentPage > 0;
  const hasNextPage = currentPage < maxPages - 1;

  const handleRejectClick = () => {
    setShowRejectDialog(true);
  };

  const handleRejectConfirm = () => {
    onReject(rejectComment);
    setRejectComment('');
    setShowRejectDialog(false);
  };

  const handleRejectCancel = () => {
    setRejectComment('');
    setShowRejectDialog(false);
  };

  // Count validated pages
  const validatedPages = Object.values(pair.pageValidations).filter(
    (v) => v.status !== null
  ).length;

  // Check if both files exist for similarity calculation
  const canCalculateSimilarity = originalPdfUrl && printerPdfUrl;

  return (
    <div className="flex flex-col gap-4 h-full">
      {/* Header with code and similarity */}
      <div className="bg-primary text-white rounded-lg p-4 flex items-center gap-6">
        {/* Code */}
        <div className="flex items-center gap-2">
          <span className="text-sm opacity-80">Code:</span>
          <span className="bg-white text-primary px-3 py-1 rounded font-mono font-bold">
            {pair.code}
          </span>
        </div>

        {/* Similarity bar or calculate button */}
        <div className="flex-1 flex items-center gap-4">
          {pair.similarity !== null || isCalculating ? (
            <SimilarityBar
              score={pair.similarity}
              threshold={threshold}
              size="md"
              isCalculating={isCalculating}
            />
          ) : canCalculateSimilarity ? (
            <Button
              variant="secondary"
              size="sm"
              onClick={onCalculateSimilarity}
              disabled={isCalculating}
              className="bg-white/20 hover:bg-white/30"
            >
              {isCalculating ? (
                <>
                  <span className="animate-spin mr-2">⏳</span>
                  Calcul en cours...
                </>
              ) : (
                <>📊 Calculer la similarité</>
              )}
            </Button>
          ) : (
            <div className="text-center text-white/70">
              Fichier manquant - Comparaison impossible
            </div>
          )}
        </div>

        {/* Threshold control */}
        <div className="flex items-center gap-2 text-sm">
          <span className="opacity-80">Seuil:</span>
          <span className="font-bold">{threshold}%</span>
        </div>
      </div>

      {/* PDFs side by side */}
      <div className="flex-1 grid grid-cols-2 gap-4 min-h-0">
        {/* Original */}
        <Card className="flex flex-col overflow-hidden">
          <div className="bg-primary text-white py-2 px-4 text-center font-semibold">
            ORIGINAL
          </div>
          <div className="flex-1 relative bg-muted min-h-[400px]">
            {originalPdfUrl ? (
              <iframe
                src={originalPdfUrl}
                title="Original PDF"
                className="w-full h-full border-0"
                style={{ minHeight: '400px' }}
              />
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <div className="text-4xl mb-2">📄</div>
                  <p>Pas de fichier original</p>
                </div>
              </div>
            )}
          </div>
          <div className="py-2 px-4 text-center text-sm text-muted-foreground border-t truncate">
            {pair.originalFile?.name || 'Aucun fichier'}
          </div>
        </Card>

        {/* Printer */}
        <Card
          className={cn(
            'flex flex-col overflow-hidden transition-all duration-500',
            pair.similarity !== null && !isCalculating
              ? pair.similarity >= threshold
                ? 'ring-4 ring-green-500'
                : 'ring-4 ring-red-500'
              : ''
          )}
        >
          <div className="bg-secondary text-white py-2 px-4 text-center font-semibold">
            IMPRIMEUR
          </div>
          <div className="flex-1 relative bg-muted min-h-[400px]">
            {printerPdfUrl ? (
              <iframe
                src={printerPdfUrl}
                title="Printer PDF"
                className="w-full h-full border-0"
                style={{ minHeight: '400px' }}
              />
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <div className="text-4xl mb-2">📄</div>
                  <p>Pas de fichier imprimeur</p>
                </div>
              </div>
            )}
          </div>
          <div className="py-2 px-4 text-center text-sm text-muted-foreground border-t truncate">
            {pair.printerFile?.name || 'Aucun fichier'}
          </div>
        </Card>
      </div>

      {/* Page navigation */}
      {maxPages > 1 && (
        <div className="flex items-center justify-center gap-4 py-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onPrevPage}
            disabled={!hasPrevPage}
          >
            ◄ Page préc.
          </Button>
          <span className="font-medium text-primary">
            Page {currentPage + 1} / {maxPages}
          </span>
          <span
            className={cn(
              'text-sm',
              validatedPages === maxPages
                ? 'text-green-600'
                : validatedPages > 0
                ? 'text-yellow-600'
                : 'text-muted-foreground'
            )}
          >
            ({validatedPages}/{maxPages} validées)
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={onNextPage}
            disabled={!hasNextPage}
          >
            Page suiv. ►
          </Button>
        </div>
      )}

      {/* PDF navigation and actions */}
      <div className="flex items-center justify-between gap-4 pt-2 border-t">
        <Button
          variant="outline"
          onClick={onPrevPair}
          disabled={!hasPrevPair}
          className="w-40"
        >
          ◄◄ PDF Précédent
        </Button>

        <div className="flex gap-4">
          <Button
            size="lg"
            className="bg-green-500 hover:bg-green-600 text-white px-8"
            onClick={onApprove}
          >
            ✓ Approuver
          </Button>
          <Button
            size="lg"
            variant="destructive"
            className="px-8"
            onClick={handleRejectClick}
          >
            ✗ Rejeter
          </Button>
        </div>

        <Button
          variant="outline"
          onClick={onNextPair}
          disabled={!hasNextPair}
          className="w-40"
        >
          PDF Suivant ►►
        </Button>
      </div>

      {/* Reject dialog */}
      {showRejectDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md p-6 space-y-4">
            <h3 className="text-lg font-semibold">Commentaire de rejet</h3>
            <textarea
              className="w-full h-24 p-2 border rounded-md resize-none"
              placeholder="Entrez un commentaire (optionnel)..."
              value={rejectComment}
              onChange={(e) => setRejectComment(e.target.value)}
              autoFocus
            />
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={handleRejectCancel}>
                Annuler
              </Button>
              <Button variant="destructive" onClick={handleRejectConfirm}>
                Confirmer le rejet
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
