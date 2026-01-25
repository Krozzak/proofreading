'use client';

import { useEffect, useState, useMemo } from 'react';
import Image from 'next/image';
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

  const [isCalculating, setIsCalculating] = useState(false);

  // Redirect if no files
  useEffect(() => {
    if (pairs.length === 0) {
      router.push('/');
    } else {
      setIsAnalyzing(false);
    }
  }, [pairs, router, setIsAnalyzing]);

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
    try {
      // Convert both PDFs to images
      const origBase64 = await fileToBase64(currentPair.originalFile.file);
      const printBase64 = await fileToBase64(currentPair.printerFile.file);

      const [origResult, printResult] = await Promise.all([
        convertPdfToImage(origBase64, currentPage),
        convertPdfToImage(printBase64, currentPage),
      ]);

      if (origResult && printResult) {
        const comparison = await compareImages(origResult.image, printResult.image);
        if (comparison) {
          updatePairSimilarity(currentIndex, comparison.similarity);
        }
      }
    } catch (error) {
      console.error('Error calculating similarity:', error);
    } finally {
      setIsCalculating(false);
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
    reset();
    router.push('/');
  };

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
          <Image
            src="/logo.png"
            alt="ProofsLab Logo"
            width={40}
            height={40}
            className="drop-shadow-lg"
          />
          <h1 className="text-xl font-bold">ProofsLab</h1>
          <span className="text-xs opacity-50">v1.1.0</span>
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
        />
      </div>

      {/* Keyboard shortcuts hint */}
      <div className="bg-muted py-2 px-6 text-center text-xs text-muted-foreground">
        Raccourcis: ←/→ Pages • Shift+←/→ PDFs • A Approuver • R Rejeter
      </div>
    </main>
  );
}
