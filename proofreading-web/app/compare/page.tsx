'use client';

import { useEffect, useState, useMemo } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { ComparisonView } from '@/components/ComparisonView';
import { ResultsTable } from '@/components/ResultsTable';
import { UserMenu } from '@/components/UserMenu';
import { PricingModal } from '@/components/PricingModal';
import { HistoryBanner } from '@/components/HistoryBanner';
import { useAppStore } from '@/lib/store';
import { useAuth } from '@/lib/auth-context';
import { useHistorySync } from '@/lib/useHistorySync';
import {
  fileToBase64,
  convertPdfToImage,
  compareImages,
  exportToCSV,
  downloadFile,
  copyToClipboard,
} from '@/lib/pdf-utils';

export default function ComparePage() {
  const router = useRouter();
  const { getIdToken, refreshQuota, quota, user } = useAuth();
  const {
    pairs,
    currentIndex,
    currentPage,
    threshold,
    showMatchedOnly,
    searchQuery,
    autoCalculate,
    restoredIndices,
    setCurrentIndex,
    setCurrentPage,
    setThreshold,
    setShowMatchedOnly,
    setSearchQuery,
    setAutoCalculate,
    validateCurrentPage,
    updatePairSimilarity,
    autoApprovePair,
    goToNextPair,
    goToPrevPair,
    goToNextPage,
    goToPrevPage,
    reset,
    setIsAnalyzing,
  } = useAppStore();

  // History sync hook (handles matching and saving in background)
  const {
    isLoadingHistory,
    matchedCount,
    showRestorePrompt,
    lastSaveTime,
    isSaving,
    restoreFromHistory,
    dismissRestorePrompt,
    forceNewVersion,
  } = useHistorySync();

  const [isCalculating, setIsCalculating] = useState(false);
  const [quotaError, setQuotaError] = useState<string | null>(null);
  const [isBatchCalculating, setIsBatchCalculating] = useState(false);
  const [batchProgress, setBatchProgress] = useState({ current: 0, total: 0 });
  const [showPricingModal, setShowPricingModal] = useState(false);

  // Only redirect if no files AND it's not a back navigation
  // We check sessionStorage to know if we had files before
  useEffect(() => {
    if (pairs.length === 0) {
      // Check if we should redirect or show empty state
      const hadSession = sessionStorage.getItem('prooflab-session-active');
      if (!hadSession) {
        router.push('/');
      }
    } else {
      setIsAnalyzing(false);
      // Mark that we have an active session
      sessionStorage.setItem('prooflab-session-active', 'true');
    }
  }, [pairs, router, setIsAnalyzing]);

  // Hydrate autoCalculate from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('prooflab-auto-calculate');
    if (stored === 'true') {
      setAutoCalculate(true);
    }
  }, [setAutoCalculate]);

  // Get current pair
  const currentPair = pairs[currentIndex];

  // Create URLs for PDF display (no server call needed!)
  const originalPdfUrl = useMemo(() => {
    const file = currentPair?.originalFile?.file;
    return file ? URL.createObjectURL(file) : null;
  }, [currentPair?.originalFile?.file]);

  const printerPdfUrl = useMemo(() => {
    const file = currentPair?.printerFile?.file;
    return file ? URL.createObjectURL(file) : null;
  }, [currentPair?.printerFile?.file]);

  // Cleanup URLs when they change
  useEffect(() => {
    return () => {
      if (originalPdfUrl) URL.revokeObjectURL(originalPdfUrl);
      if (printerPdfUrl) URL.revokeObjectURL(printerPdfUrl);
    };
  }, [originalPdfUrl, printerPdfUrl]);

  // Calculate similarity on demand (only when user clicks button)
  const handleCalculateSimilarity = async () => {
    if (!currentPair?.originalFile?.file || !currentPair?.printerFile?.file) {
      return;
    }

    setIsCalculating(true);
    setQuotaError(null);

    try {
      // Get auth token if logged in
      const token = await getIdToken();

      // Convert both PDFs to images
      const origBase64 = await fileToBase64(currentPair.originalFile.file);
      const printBase64 = await fileToBase64(currentPair.printerFile.file);

      const [origResult, printResult] = await Promise.all([
        convertPdfToImage(origBase64, currentPage, token),
        convertPdfToImage(printBase64, currentPage, token),
      ]);

      if (origResult && printResult) {
        const comparison = await compareImages(origResult.image, printResult.image, true, token);
        if (comparison) {
          updatePairSimilarity(currentIndex, comparison.similarity);
          // Refresh quota display after successful comparison
          await refreshQuota();
        }
      }
    } catch (error) {
      console.error('Error calculating similarity:', error);
      const errorMessage = error instanceof Error ? error.message : 'Erreur inconnue';

      // Handle quota exceeded error
      if (errorMessage.includes('429') || errorMessage.toLowerCase().includes('quota')) {
        setQuotaError(errorMessage);
      }
    } finally {
      setIsCalculating(false);
    }
  };

  // Auto-calculate similarity when enabled and conditions are met
  useEffect(() => {
    if (
      autoCalculate &&
      currentPair?.originalFile?.file &&
      currentPair?.printerFile?.file &&
      currentPair.similarity === null &&
      !isCalculating &&
      !isBatchCalculating &&
      quota &&
      quota.remaining > 0
    ) {
      handleCalculateSimilarity();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoCalculate, currentIndex, currentPair?.similarity]);

  // Calculate all similarities in batch
  const handleCalculateAll = async () => {
    const pairsToCalculate = pairs
      .map((pair, index) => ({ pair, index }))
      .filter(
        ({ pair }) =>
          pair.originalFile?.file &&
          pair.printerFile?.file &&
          pair.similarity === null
      );

    if (pairsToCalculate.length === 0) {
      alert('Toutes les similarités sont déjà calculées !');
      return;
    }

    // Check initial quota
    await refreshQuota();
    if (!quota || quota.remaining < 1) {
      setQuotaError('Quota insuffisant pour calculer les similarités');
      return;
    }

    setIsBatchCalculating(true);
    setBatchProgress({ current: 0, total: pairsToCalculate.length });
    setQuotaError(null);

    const token = await getIdToken();

    for (let i = 0; i < pairsToCalculate.length; i++) {
      const { pair, index } = pairsToCalculate[i];

      try {
        const origBase64 = await fileToBase64(pair.originalFile!.file!);
        const printBase64 = await fileToBase64(pair.printerFile!.file!);

        const [origResult, printResult] = await Promise.all([
          convertPdfToImage(origBase64, 0, token),
          convertPdfToImage(printBase64, 0, token),
        ]);

        if (origResult && printResult) {
          const comparison = await compareImages(
            origResult.image,
            printResult.image,
            true,
            token
          );
          if (comparison) {
            updatePairSimilarity(index, comparison.similarity);
          }
        }

        setBatchProgress({ current: i + 1, total: pairsToCalculate.length });
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Erreur';
        if (errorMessage.includes('429') || errorMessage.toLowerCase().includes('quota')) {
          setQuotaError(`Quota épuisé après ${i} calcul(s)`);
          break;
        }
        console.error(`Error calculating pair ${index}:`, error);
      }
    }

    setIsBatchCalculating(false);
    await refreshQuota();
  };

  // Auto-approve all files above threshold
  const handleAutoApprove = () => {
    const eligiblePairs = pairs.filter(
      (pair, index) =>
        pair.similarity !== null &&
        pair.similarity >= threshold &&
        pair.validation !== 'approved'
    );

    if (eligiblePairs.length === 0) {
      alert('Aucun fichier éligible à l\'auto-approbation');
      return;
    }

    const confirmed = window.confirm(
      `Approuver automatiquement ${eligiblePairs.length} fichier(s) avec similarité >= ${threshold}% ?`
    );

    if (confirmed) {
      eligiblePairs.forEach((pair) => {
        const index = pairs.indexOf(pair);
        autoApprovePair(index);
      });
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if typing in input
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      switch (e.key) {
        case 'ArrowLeft':
          if (e.shiftKey) {
            goToPrevPair();
          } else {
            goToPrevPage();
          }
          break;
        case 'ArrowRight':
          if (e.shiftKey) {
            goToNextPair();
          } else {
            goToNextPage();
          }
          break;
        case 'a':
        case 'A':
          validateCurrentPage('approved');
          break;
        case 'r':
        case 'R':
          // For reject, we need the dialog, so don't handle here
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [goToPrevPair, goToNextPair, goToPrevPage, goToNextPage, validateCurrentPage]);

  const handleApprove = () => {
    validateCurrentPage('approved');
  };

  const handleReject = (comment: string) => {
    validateCurrentPage('rejected', comment);
  };

  const handleExportCSV = () => {
    const data = pairs.map((pair) => ({
      code: pair.code,
      filename: pair.originalFile?.name || pair.printerFile?.name || '',
      matching:
        pair.originalFile && pair.printerFile
          ? 'Les deux'
          : pair.originalFile
          ? 'Original seul'
          : 'Imprimeur seul',
      similarity: pair.similarity !== null ? `${Math.round(pair.similarity)}%` : 'N/A',
      validation:
        pair.validation === 'approved'
          ? 'Approuvé'
          : pair.validation === 'rejected'
          ? 'Rejeté'
          : pair.validation === 'partial'
          ? 'Partiel'
          : 'En attente',
      comment: pair.comment,
      date: pair.validatedAt || '',
    }));

    const csv = exportToCSV(data);
    const timestamp = new Date().toISOString().slice(0, 10);
    downloadFile(csv, `proofreading_export_${timestamp}.csv`);
  };

  const handleCopyClipboard = async () => {
    const data = pairs.map((pair) => ({
      code: pair.code,
      filename: pair.originalFile?.name || pair.printerFile?.name || '',
      matching:
        pair.originalFile && pair.printerFile
          ? 'Les deux'
          : pair.originalFile
          ? 'Original seul'
          : 'Imprimeur seul',
      similarity: pair.similarity !== null ? `${Math.round(pair.similarity)}%` : 'N/A',
      validation:
        pair.validation === 'approved'
          ? 'Approuvé'
          : pair.validation === 'rejected'
          ? 'Rejeté'
          : pair.validation === 'partial'
          ? 'Partiel'
          : 'En attente',
      comment: pair.comment,
      date: pair.validatedAt || '',
    }));

    // Tab-separated for Excel paste
    const headers = ['Code Litho', 'Filename', 'Matching', 'Similarity', 'Validation', 'Comment', 'Date'];
    const rows = data.map((row) => Object.values(row).join('\t'));
    const content = [headers.join('\t'), ...rows].join('\n');

    const success = await copyToClipboard(content);
    if (success) {
      alert('Données copiées dans le presse-papiers !');
    }
  };

  const handleBack = () => {
    // Clear session marker when explicitly going back
    sessionStorage.removeItem('prooflab-session-active');
    reset();
    router.push('/');
  };

  if (pairs.length === 0) {
    // Check if session was lost (e.g., page refresh)
    const hadSession = typeof window !== 'undefined' && sessionStorage.getItem('prooflab-session-active');

    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center max-w-md">
          {hadSession ? (
            <>
              <p className="text-lg font-medium mb-2">Session expirée</p>
              <p className="text-muted-foreground mb-4">
                Les données de comparaison ont été perdues suite à un rechargement de page.
                Veuillez recommencer l&apos;analyse.
              </p>
            </>
          ) : (
            <p className="text-muted-foreground mb-4">Aucun fichier à comparer</p>
          )}
          <Link href="/">
            <Button onClick={() => sessionStorage.removeItem('prooflab-session-active')}>
              Retour à l&apos;accueil
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen flex flex-col">
      {/* Fixed header + error banner */}
      <div className="sticky top-0 z-50">
        {/* Header */}
        <header className="bg-primary text-white py-3 px-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Image
              src="/logo.png"
              alt="ProofsLab Logo"
              width={40}
              height={40}
              className="drop-shadow-lg"
            />
            <h1 className="text-xl font-bold">ProofsLab</h1>
            <span className="text-xs opacity-50">v1.2.0</span>
            <span className="text-sm opacity-70">
              {currentIndex + 1} / {pairs.length} fichiers
            </span>
          </div>

          <div className="flex items-center gap-4">
            {/* Auto-calculate toggle */}
            <div className="flex items-center gap-2 bg-white/10 rounded-lg px-3 py-1">
              <label htmlFor="auto-calc" className="text-sm cursor-pointer">
                Auto-calcul:
              </label>
              <input
                type="checkbox"
                id="auto-calc"
                checked={autoCalculate}
                onChange={(e) => setAutoCalculate(e.target.checked)}
                className="w-4 h-4 cursor-pointer accent-white"
              />
              {autoCalculate && quota && quota.remaining <= 3 && (
                <span className="text-yellow-300 text-xs ml-1">
                  ({quota.remaining} restants)
                </span>
              )}
            </div>

            {/* Threshold control */}
            <div className="flex items-center gap-2 bg-white/10 rounded-lg px-3 py-1">
              <span className="text-sm">Seuil:</span>
              <Slider
                value={[threshold]}
                onValueChange={(value) => setThreshold(value[0])}
                min={50}
                max={100}
                step={1}
                className="w-24"
              />
              <span className="text-sm font-bold w-10">{threshold}%</span>
            </div>

            <UserMenu />

            <Button variant="secondary" size="sm" onClick={handleBack}>
              ← Retour
            </Button>
          </div>
        </header>

        {/* Quota error banner */}
        {quotaError && (
          <div className="bg-red-100 border-b border-red-300 px-6 py-3 text-center">
            <p className="text-red-700 font-medium">
              {quotaError}
              {' — '}
              <button
                onClick={() => setShowPricingModal(true)}
                className="underline hover:no-underline font-bold"
              >
                Passer au plan Pro
              </button>
            </p>
          </div>
        )}

        {/* History restore banner */}
        {user && showRestorePrompt && (
          <HistoryBanner
            matchedCount={matchedCount}
            onRestore={restoreFromHistory}
            onNewVersion={forceNewVersion}
            onDismiss={dismissRestorePrompt}
          />
        )}
      </div>

      {/* Main comparison area */}
      <div className="flex-1 p-6 overflow-auto">
        {currentPair ? (
          <ComparisonView
            pair={currentPair}
            originalPdfUrl={originalPdfUrl}
            printerPdfUrl={printerPdfUrl}
            currentPage={currentPage}
            threshold={threshold}
            onApprove={handleApprove}
            onReject={handleReject}
            onPrevPage={goToPrevPage}
            onNextPage={goToNextPage}
            onPrevPair={goToPrevPair}
            onNextPair={goToNextPair}
            hasPrevPair={currentIndex > 0}
            hasNextPair={currentIndex < pairs.length - 1}
            onCalculateSimilarity={handleCalculateSimilarity}
            isCalculating={isCalculating}
          />
        ) : null}
      </div>

      {/* Results table */}
      <div className="border-t bg-muted/30 p-4">
        <ResultsTable
          pairs={pairs}
          currentIndex={currentIndex}
          onSelectPair={setCurrentIndex}
          onExportCSV={handleExportCSV}
          onCopyClipboard={handleCopyClipboard}
          showMatchedOnly={showMatchedOnly}
          onToggleFilter={() => setShowMatchedOnly(!showMatchedOnly)}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          onCalculateAll={handleCalculateAll}
          isBatchCalculating={isBatchCalculating}
          batchProgress={batchProgress}
          onAutoApprove={handleAutoApprove}
          threshold={threshold}
          restoredIndices={restoredIndices}
        />
      </div>

      {/* Keyboard shortcuts hint */}
      <div className="bg-muted py-2 px-6 text-center text-xs text-muted-foreground">
        Raccourcis: ←/→ Pages • Shift+←/→ PDFs • A Approuver • R Rejeter
      </div>

      {/* Pricing modal */}
      <PricingModal
        isOpen={showPricingModal}
        onClose={() => setShowPricingModal(false)}
      />
    </main>
  );
}
