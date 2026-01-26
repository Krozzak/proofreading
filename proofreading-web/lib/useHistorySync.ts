'use client';

/**
 * Hook for synchronizing comparison history with Firebase.
 * Handles:
 * - Non-blocking history matching on page load
 * - Debounced saving of validation changes
 * - beforeunload save
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { useAuth } from './auth-context';
import { useAppStore } from './store';
import {
  generateFileSignature,
  saveComparisonHistory,
  matchFilesFromHistory,
  fileToHistoryInfo,
} from './history-api';
import type { SavedComparison, HistoryMatch } from './types';

// Debounce delays
const VALIDATION_SAVE_DELAY = 2000; // 2 seconds after validation
const SIMILARITY_SAVE_DELAY = 5000; // 5 seconds after similarity calc
const BATCH_SAVE_THRESHOLD = 10; // Save immediately if 10+ pending

export interface HistorySyncState {
  isLoadingHistory: boolean;
  matchedCount: number;
  historyMatches: Map<string, HistoryMatch>;
  showRestorePrompt: boolean;
  lastSaveTime: Date | null;
  isSaving: boolean;
}

export interface HistorySyncActions {
  restoreFromHistory: () => void;
  dismissRestorePrompt: () => void;
  forceNewVersion: () => void;
}

export function useHistorySync(): HistorySyncState & HistorySyncActions {
  const { user, getIdToken } = useAuth();
  const {
    pairs,
    fileSignatures,
    setFileSignatures,
    pendingSaveIndices,
    clearPendingSaves,
    applyHistoryMatch,
    markPairsAsRestored,
  } = useAppStore();

  // State
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [historyMatches, setHistoryMatches] = useState<Map<string, HistoryMatch>>(
    new Map()
  );
  const [showRestorePrompt, setShowRestorePrompt] = useState(false);
  const [lastSaveTime, setLastSaveTime] = useState<Date | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  // Refs for debouncing
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pendingSignaturesRef = useRef<string[]>([]);

  // Compute file signatures when pairs change
  useEffect(() => {
    const computeSignatures = async () => {
      if (pairs.length === 0) return;

      const signatures = new Map<number, string>();

      for (let i = 0; i < pairs.length; i++) {
        const pair = pairs[i];
        const sig = await generateFileSignature(
          pair.originalFile?.name || null,
          pair.originalFile?.file?.size || null,
          pair.printerFile?.name || null,
          pair.printerFile?.file?.size || null
        );
        signatures.set(i, sig);
      }

      setFileSignatures(signatures);
    };

    computeSignatures();
  }, [pairs.length]); // Only recompute when pairs length changes

  // Match history when signatures are computed and user is logged in
  useEffect(() => {
    const matchHistory = async () => {
      if (!user || fileSignatures.size === 0) return;

      setIsLoadingHistory(true);

      try {
        const token = await getIdToken();
        if (!token) return;

        const signatureList = Array.from(fileSignatures.values());
        const matches = await matchFilesFromHistory(token, signatureList);

        const matchesMap = new Map(Object.entries(matches));
        setHistoryMatches(matchesMap);

        // Show prompt if we found matches
        if (matchesMap.size > 0) {
          setShowRestorePrompt(true);
        }
      } catch (error) {
        console.error('Failed to match history:', error);
      } finally {
        setIsLoadingHistory(false);
      }
    };

    matchHistory();
  }, [user, fileSignatures, getIdToken]);

  // Save pending changes
  const savePendingChanges = useCallback(async () => {
    if (!user || pendingSaveIndices.size === 0) return;

    setIsSaving(true);

    try {
      const token = await getIdToken();
      if (!token) return;

      const comparisonsToSave: SavedComparison[] = [];

      for (const index of pendingSaveIndices) {
        const pair = pairs[index];
        const signature = fileSignatures.get(index);

        if (!pair || !signature) continue;

        // Convert pageValidations keys to strings
        const pageValidations: Record<string, { status: 'approved' | 'rejected' | null; comment?: string }> = {};
        Object.entries(pair.pageValidations).forEach(([key, value]) => {
          pageValidations[key] = {
            status: value.status,
            comment: value.comment,
          };
        });

        comparisonsToSave.push({
          fileSignature: signature,
          code: pair.code,
          originalFile: fileToHistoryInfo(pair.originalFile?.file),
          printerFile: fileToHistoryInfo(pair.printerFile?.file),
          similarity: pair.similarity,
          validation: pair.validation,
          pageValidations,
          comment: pair.comment,
          validatedAt: pair.validatedAt,
        });
      }

      if (comparisonsToSave.length > 0) {
        await saveComparisonHistory(token, comparisonsToSave);
        clearPendingSaves();
        setLastSaveTime(new Date());
      }
    } catch (error) {
      console.error('Failed to save history:', error);
    } finally {
      setIsSaving(false);
    }
  }, [user, pairs, fileSignatures, pendingSaveIndices, getIdToken, clearPendingSaves]);

  // Debounced save when pending changes accumulate
  useEffect(() => {
    if (!user || pendingSaveIndices.size === 0) return;

    // Clear existing timeout
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    // Save immediately if batch threshold reached
    if (pendingSaveIndices.size >= BATCH_SAVE_THRESHOLD) {
      savePendingChanges();
      return;
    }

    // Otherwise, debounce
    saveTimeoutRef.current = setTimeout(() => {
      savePendingChanges();
    }, VALIDATION_SAVE_DELAY);

    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [user, pendingSaveIndices.size, savePendingChanges]);

  // Save on beforeunload
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (user && pendingSaveIndices.size > 0) {
        // Use sendBeacon for reliable unload saving
        // Note: This is a simplified version; full implementation would use sendBeacon
        savePendingChanges();
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [user, pendingSaveIndices.size, savePendingChanges]);

  // Restore from history action
  const restoreFromHistory = useCallback(() => {
    const indicesToRestore: number[] = [];

    fileSignatures.forEach((signature, index) => {
      const match = historyMatches.get(signature);
      if (match) {
        applyHistoryMatch(index, match);
        indicesToRestore.push(index);
      }
    });

    markPairsAsRestored(indicesToRestore);
    setShowRestorePrompt(false);
  }, [fileSignatures, historyMatches, applyHistoryMatch, markPairsAsRestored]);

  // Dismiss restore prompt (keep current state)
  const dismissRestorePrompt = useCallback(() => {
    setShowRestorePrompt(false);
  }, []);

  // Force new version (clear matches, don't restore)
  const forceNewVersion = useCallback(() => {
    setHistoryMatches(new Map());
    setShowRestorePrompt(false);
  }, []);

  return {
    isLoadingHistory,
    matchedCount: historyMatches.size,
    historyMatches,
    showRestorePrompt,
    lastSaveTime,
    isSaving,
    restoreFromHistory,
    dismissRestorePrompt,
    forceNewVersion,
  };
}
