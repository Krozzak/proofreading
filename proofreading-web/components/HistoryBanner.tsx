'use client';

/**
 * Banner component to notify user about files found in history.
 * Non-blocking - user can continue working while this is visible.
 */

import { Button } from '@/components/ui/button';

interface HistoryBannerProps {
  matchedCount: number;
  onRestore: () => void;
  onNewVersion: () => void;
  onDismiss: () => void;
}

export function HistoryBanner({
  matchedCount,
  onRestore,
  onNewVersion,
  onDismiss,
}: HistoryBannerProps) {
  return (
    <div className="bg-blue-50 border-b border-blue-200 px-6 py-3">
      <div className="flex items-center justify-between max-w-4xl mx-auto">
        <div className="flex items-center gap-3">
          <span className="text-2xl">📂</span>
          <div>
            <p className="text-blue-800 font-medium">
              {matchedCount} fichier{matchedCount > 1 ? 's' : ''} trouvé{matchedCount > 1 ? 's' : ''} dans l&apos;historique
            </p>
            <p className="text-blue-600 text-sm">
              Ces fichiers ont déjà été comparés. Voulez-vous restaurer les résultats précédents ?
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="default"
            size="sm"
            onClick={onRestore}
            className="bg-blue-600 hover:bg-blue-700"
          >
            Restaurer l&apos;historique
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={onNewVersion}
          >
            Nouvelle version
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={onDismiss}
            className="text-blue-600 hover:text-blue-800"
          >
            Ignorer
          </Button>
        </div>
      </div>
    </div>
  );
}
