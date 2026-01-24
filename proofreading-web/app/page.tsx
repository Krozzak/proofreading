'use client';

import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { DropZone } from '@/components/DropZone';
import { useAppStore, createPairsFromFiles } from '@/lib/store';

export default function HomePage() {
  const router = useRouter();
  const {
    originalFiles,
    printerFiles,
    threshold,
    isAnalyzing,
    setOriginalFiles,
    setPrinterFiles,
    setThreshold,
    setPairs,
    setIsAnalyzing,
  } = useAppStore();

  const canStartAnalysis = originalFiles.length > 0 || printerFiles.length > 0;

  const handleStartAnalysis = async () => {
    if (!canStartAnalysis) return;

    setIsAnalyzing(true);

    // Create pairs from files
    const pairs = createPairsFromFiles(originalFiles, printerFiles);
    setPairs(pairs);

    // Navigate to comparison page
    router.push('/compare');
  };

  return (
    <main className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-primary text-white py-6 px-8">
        <div className="max-w-6xl mx-auto text-center">
          <h1 className="text-3xl font-bold tracking-tight">
            PRINTER PROOFREADING
          </h1>
          <p className="mt-2 text-primary-foreground/80">
            Comparez vos fichiers imprimés avec les originaux
          </p>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 max-w-6xl mx-auto w-full px-8 py-12">
        {/* Instructions */}
        <div className="text-center mb-10">
          <h2 className="text-xl font-medium text-foreground">
            Sélectionnez les dossiers à comparer
          </h2>
          <p className="mt-2 text-muted-foreground">
            Glissez vos dossiers PDF ou cliquez pour sélectionner les fichiers
          </p>
        </div>

        {/* Drop zones */}
        <div className="grid md:grid-cols-2 gap-8 mb-10">
          <DropZone
            title="DOSSIER ORIGINAL"
            description="Fichiers design originaux"
            accentColor="primary"
            files={originalFiles}
            onFilesChange={setOriginalFiles}
          />
          <DropZone
            title="DOSSIER IMPRIMEUR"
            description="Fichiers de l'imprimeur"
            accentColor="secondary"
            files={printerFiles}
            onFilesChange={setPrinterFiles}
          />
        </div>

        {/* Threshold setting */}
        <div className="max-w-md mx-auto mb-10">
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-foreground">
              Seuil de similarité
            </label>
            <span className="text-sm font-bold text-primary">{threshold}%</span>
          </div>
          <Slider
            value={[threshold]}
            onValueChange={(value) => setThreshold(value[0])}
            min={50}
            max={100}
            step={1}
            className="w-full"
          />
          <p className="text-xs text-muted-foreground mt-2 text-center">
            Les fichiers avec une similarité inférieure à ce seuil seront marqués comme non conformes
          </p>
        </div>

        {/* Start button */}
        <div className="text-center">
          <Button
            size="lg"
            disabled={!canStartAnalysis || isAnalyzing}
            onClick={handleStartAnalysis}
            className="px-12 py-6 text-lg font-semibold"
          >
            {isAnalyzing ? (
              <>
                <span className="animate-spin mr-2">⏳</span>
                Analyse en cours...
              </>
            ) : (
              "COMMENCER L'ANALYSE"
            )}
          </Button>

          {canStartAnalysis && (
            <p className="mt-4 text-sm text-muted-foreground">
              {originalFiles.length} fichier{originalFiles.length > 1 ? 's' : ''} original
              {originalFiles.length > 1 ? 's' : ''} • {printerFiles.length} fichier
              {printerFiles.length > 1 ? 's' : ''} imprimeur
            </p>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="py-4 text-center text-sm text-muted-foreground border-t">
        <p>Printer Proofreading v4.0 • Comparaison SSIM</p>
      </footer>
    </main>
  );
}
