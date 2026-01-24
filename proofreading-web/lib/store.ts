import { create } from 'zustand';
import type { ComparisonPair, PageValidation } from './types';

interface AppState {
  // Upload state
  originalFiles: File[];
  printerFiles: File[];
  setOriginalFiles: (files: File[]) => void;
  setPrinterFiles: (files: File[]) => void;

  // Comparison state
  pairs: ComparisonPair[];
  currentIndex: number;
  currentPage: number;
  threshold: number;
  isAnalyzing: boolean;
  showMatchedOnly: boolean;

  setPairs: (pairs: ComparisonPair[]) => void;
  setCurrentIndex: (index: number) => void;
  setCurrentPage: (page: number) => void;
  setThreshold: (threshold: number) => void;
  setIsAnalyzing: (isAnalyzing: boolean) => void;
  setShowMatchedOnly: (show: boolean) => void;

  // Validation
  validateCurrentPage: (status: 'approved' | 'rejected', comment?: string) => void;
  updatePairSimilarity: (index: number, similarity: number) => void;

  // Navigation helpers
  goToNextPair: () => void;
  goToPrevPair: () => void;
  goToNextPage: () => void;
  goToPrevPage: () => void;

  // Reset
  reset: () => void;
}

const extractCode = (filename: string): string => {
  return filename.slice(0, 8);
};

export const useAppStore = create<AppState>((set, get) => ({
  // Initial state
  originalFiles: [],
  printerFiles: [],
  pairs: [],
  currentIndex: 0,
  currentPage: 0,
  threshold: 85,
  isAnalyzing: false,
  showMatchedOnly: false,

  // Setters
  setOriginalFiles: (files) => set({ originalFiles: files }),
  setPrinterFiles: (files) => set({ printerFiles: files }),
  setPairs: (pairs) => set({ pairs }),
  setCurrentIndex: (index) => set({ currentIndex: index, currentPage: 0 }),
  setCurrentPage: (page) => set({ currentPage: page }),
  setThreshold: (threshold) => set({ threshold }),
  setIsAnalyzing: (isAnalyzing) => set({ isAnalyzing }),
  setShowMatchedOnly: (show) => set({ showMatchedOnly: show }),

  // Validation
  validateCurrentPage: (status, comment = '') => {
    const { pairs, currentIndex, currentPage } = get();
    const pair = pairs[currentIndex];
    if (!pair) return;

    const maxPages = Math.max(pair.totalPagesOriginal, pair.totalPagesPrinter);
    const newPageValidations = {
      ...pair.pageValidations,
      [currentPage]: { status, comment } as PageValidation,
    };

    // Calculate overall validation status
    const validatedCount = Object.values(newPageValidations).filter(
      (v) => v.status !== null
    ).length;
    const hasRejected = Object.values(newPageValidations).some(
      (v) => v.status === 'rejected'
    );

    let validation: ComparisonPair['validation'] = 'pending';
    if (validatedCount === maxPages) {
      validation = hasRejected ? 'rejected' : 'approved';
    } else if (validatedCount > 0) {
      validation = 'partial';
    }

    const updatedPairs = [...pairs];
    updatedPairs[currentIndex] = {
      ...pair,
      pageValidations: newPageValidations,
      validation,
      comment: status === 'rejected' ? comment : pair.comment,
      validatedAt: new Date().toISOString(),
    };

    set({ pairs: updatedPairs });

    // Auto-navigate
    if (currentPage < maxPages - 1) {
      // Go to next page
      set({ currentPage: currentPage + 1 });
    } else if (currentIndex < pairs.length - 1) {
      // Go to next pair
      set({ currentIndex: currentIndex + 1, currentPage: 0 });
    }
  },

  updatePairSimilarity: (index, similarity) => {
    const { pairs } = get();
    const updatedPairs = [...pairs];
    if (updatedPairs[index]) {
      updatedPairs[index] = { ...updatedPairs[index], similarity };
      set({ pairs: updatedPairs });
    }
  },

  // Navigation
  goToNextPair: () => {
    const { currentIndex, pairs } = get();
    if (currentIndex < pairs.length - 1) {
      set({ currentIndex: currentIndex + 1, currentPage: 0 });
    }
  },

  goToPrevPair: () => {
    const { currentIndex } = get();
    if (currentIndex > 0) {
      set({ currentIndex: currentIndex - 1, currentPage: 0 });
    }
  },

  goToNextPage: () => {
    const { currentPage, pairs, currentIndex } = get();
    const pair = pairs[currentIndex];
    if (!pair) return;
    const maxPages = Math.max(pair.totalPagesOriginal, pair.totalPagesPrinter);
    if (currentPage < maxPages - 1) {
      set({ currentPage: currentPage + 1 });
    }
  },

  goToPrevPage: () => {
    const { currentPage } = get();
    if (currentPage > 0) {
      set({ currentPage: currentPage - 1 });
    }
  },

  // Reset
  reset: () =>
    set({
      originalFiles: [],
      printerFiles: [],
      pairs: [],
      currentIndex: 0,
      currentPage: 0,
      isAnalyzing: false,
    }),
}));

// Helper function to match files and create pairs
export function createPairsFromFiles(
  originalFiles: File[],
  printerFiles: File[]
): ComparisonPair[] {
  const pairs: ComparisonPair[] = [];
  const usedPrinterCodes = new Set<string>();

  // First, match original files with printer files
  originalFiles.forEach((file, idx) => {
    const code = extractCode(file.name);
    const matchingPrinter = printerFiles.find(
      (pf) => extractCode(pf.name) === code
    );

    if (matchingPrinter) {
      usedPrinterCodes.add(code);
    }

    pairs.push({
      index: idx,
      code,
      originalFile: {
        name: file.name,
        path: file.name,
        code,
        file, // Store the actual File object
      },
      printerFile: matchingPrinter
        ? {
            name: matchingPrinter.name,
            path: matchingPrinter.name,
            code,
            file: matchingPrinter, // Store the actual File object
          }
        : null,
      similarity: null,
      totalPagesOriginal: 1, // Will be updated after processing
      totalPagesPrinter: matchingPrinter ? 1 : 0,
      validation: 'pending',
      pageValidations: {},
      comment: '',
      validatedAt: null,
    });
  });

  // Add printer-only files
  printerFiles.forEach((file) => {
    const code = extractCode(file.name);
    if (!usedPrinterCodes.has(code)) {
      pairs.push({
        index: pairs.length,
        code,
        originalFile: null,
        printerFile: {
          name: file.name,
          path: file.name,
          code,
          file, // Store the actual File object
        },
        similarity: null,
        totalPagesOriginal: 0,
        totalPagesPrinter: 1,
        validation: 'pending',
        pageValidations: {},
        comment: '',
        validatedAt: null,
      });
    }
  });

  return pairs;
}
