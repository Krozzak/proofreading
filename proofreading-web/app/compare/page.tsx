'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { ComparisonView } from '@/components/ComparisonView';
import { ResultsTable } from '@/components/ResultsTable';
import { useAppStore } from '@/lib/store';
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
  const {
    pairs,
    currentIndex,
    currentPage,
    threshold,
    originalFiles,
    printerFiles,
    showMatchedOnly,
    setCurrentIndex,
    setCurrentPage,
    setThreshold,
    setShowMatchedOnly,
    validateCurrentPage,
    updatePairSimilarity,
    goToNextPair,
    goToPrevPair,
    goToNextPage,
    goToPrevPage,
    reset,
    setIsAnalyzing,
  } = useAppStore();

  const [originalImage, setOriginalImage] = useState<string | null>(null);
  const [printerImage, setPrinterImage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [processedCount, setProcessedCount] = useState(0);

  // Redirect if no files
  useEffect(() => {
    if (pairs.length === 0) {
      router.push('/');
    } else {
      setIsAnalyzing(false);
    }
  }, [pairs, router, setIsAnalyzing]);

  // Load images when current pair or page changes
  const loadImages = useCallback(async () => {
    if (pairs.length === 0) return;

    const pair = pairs[currentIndex];
    if (!pair) return;

    setIsLoading(true);
    setOriginalImage(null);
    setPrinterImage(null);

    try {
      // Find the actual File objects
      const originalFile = pair.originalFile
        ? originalFiles.find((f) => f.name === pair.originalFile?.name)
        : null;
      const printerFile = pair.printerFile
        ? printerFiles.find((f) => f.name === pair.printerFile?.name)
        : null;

      let origImg: string | null = null;
      let printImg: string | null = null;
      let origPages = 1;
      let printPages = 1;

      // Convert PDFs to images
      if (originalFile) {
        const base64 = await fileToBase64(originalFile);
        const result = await convertPdfToImage(base64, currentPage);
        if (result) {
          origImg = result.image;
          origPages = result.totalPages;
        }
      }

      if (printerFile) {
        const base64 = await fileToBase64(printerFile);
        const result = await convertPdfToImage(base64, currentPage);
        if (result) {
          printImg = result.image;
          printPages = result.totalPages;
        }
      }

      setOriginalImage(origImg);
      setPrinterImage(printImg);

      // Update page counts in pair if needed
      if (origPages > 1 || printPages > 1) {
        // Update pair with page counts (would need store update)
      }

      // Calculate similarity if both images exist
      if (origImg && printImg) {
        const comparison = await compareImages(origImg, printImg);
        if (comparison) {
          updatePairSimilarity(currentIndex, comparison.similarity);
        }
      }
    } catch (error) {
      console.error('Error loading images:', error);
    } finally {
      setIsLoading(false);
    }
  }, [pairs, currentIndex, currentPage, originalFiles, printerFiles, updatePairSimilarity]);

  useEffect(() => {
    loadImages();
  }, [loadImages]);

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
    reset();
    router.push('/');
  };

  const currentPair = pairs[currentIndex];

  if (pairs.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-muted-foreground mb-4">Aucun fichier à comparer</p>
          <Link href="/">
            <Button>Retour à l&apos;accueil</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-primary text-white py-3 px-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold">PRINTER PROOFREADING</h1>
          <span className="text-sm opacity-70">
            {currentIndex + 1} / {pairs.length} fichiers
          </span>
        </div>

        <div className="flex items-center gap-4">
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

          <Button variant="secondary" size="sm" onClick={handleBack}>
            ← Retour
          </Button>
        </div>
      </header>

      {/* Main comparison area */}
      <div className="flex-1 p-6 overflow-hidden">
        {isLoading ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin text-4xl mb-4">⏳</div>
              <p className="text-muted-foreground">Chargement des images...</p>
            </div>
          </div>
        ) : currentPair ? (
          <ComparisonView
            pair={currentPair}
            originalImage={originalImage}
            printerImage={printerImage}
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
        />
      </div>

      {/* Keyboard shortcuts hint */}
      <div className="bg-muted py-2 px-6 text-center text-xs text-muted-foreground">
        Raccourcis: ←/→ Pages • Shift+←/→ PDFs • A Approuver • R Rejeter
      </div>
    </main>
  );
}
