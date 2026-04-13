'use client';

import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { DropZone } from '@/components/DropZone';
import { UserMenu } from '@/components/UserMenu';
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
    const pairs = createPairsFromFiles(originalFiles, printerFiles);
    setPairs(pairs);
    router.push('/compare');
  };

  return (
    <main className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-primary text-white py-5 px-8 shadow-sm">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Image
              src="/logo.png"
              alt="ProofsLab Logo"
              width={48}
              height={48}
              className="drop-shadow-lg"
            />
            <h1 className="text-2xl font-bold tracking-tight">
              ProofsLab
              <span className="ml-2 text-xs opacity-40 font-normal align-middle">v1.3.0</span>
            </h1>
          </div>
          <UserMenu />
        </div>
      </header>

      {/* Hero */}
      <div className="bg-background border-b py-12 px-8">
        <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-12 items-center">
          {/* Texte */}
          <div className="flex flex-col gap-5">
            <h2 className="text-3xl font-bold tracking-tight text-foreground leading-snug">
              Validez vos fichiers imprimeur<br />
              <span className="text-primary">en quelques minutes.</span>
            </h2>
            <p className="text-muted-foreground text-base leading-relaxed">
              Comparez vos PDF originaux avec les fichiers imprimeur — page par page, pixel par pixel.
              ProofsLab calcule un score de similarité et vous permet d&apos;approuver ou rejeter chaque fichier en un clic.
            </p>
            <div>
              <a href="#vos-fichiers">
                <Button size="lg" className="px-8 py-5 text-base font-semibold">
                  Commencer l&apos;analyse →
                </Button>
              </a>
            </div>
          </div>

          {/* Illustration */}
          <div className="rounded-xl overflow-hidden shadow-lg border border-border">
            <Image
              src="/hero-preview.png"
              alt="Interface ProofsLab — comparaison de deux PDF côte à côte avec score de similarité"
              width={800}
              height={450}
              className="w-full h-auto"
              priority
            />
          </div>
        </div>
      </div>

      {/* Stepper — Comment ça marche */}
      <div className="bg-muted/30 border-b py-10 px-8">
        <div className="max-w-4xl mx-auto">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-8 text-center">
            Comment ça marche
          </p>

          <div className="relative grid md:grid-cols-3 gap-6">
            {/* Ligne de connexion desktop — centrée sur les cercles (h-10 = 2.5rem, centre = 1.25rem) */}
            <div className="hidden md:block absolute top-[1.25rem] left-[calc(33.33%-1.25rem)] right-[calc(33.33%-1.25rem)] h-px bg-border z-0" />

            {/* Étape 1 */}
            <div className="relative z-10 bg-card rounded-xl p-6 shadow-sm border border-border flex flex-col gap-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold shrink-0">
                  1
                </div>
                <h3 className="font-semibold text-foreground">Déposez vos PDF</h3>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Glissez vos fichiers <strong className="text-foreground">Originaux</strong> (design)
                et vos fichiers <strong className="text-foreground">Imprimeur</strong>.
                ProofsLab les associe automatiquement.
              </p>
              <div className="mt-1 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-xs text-amber-800">
                <strong>Règle :</strong> association par les 8 premiers caractères du nom.{' '}
                <span className="font-mono bg-amber-100 px-1 rounded">12345678_design.pdf</span>
                {' ↔ '}
                <span className="font-mono bg-amber-100 px-1 rounded">12345678_print.pdf</span>
              </div>
            </div>

            {/* Étape 2 */}
            <div className="relative z-10 bg-card rounded-xl p-6 shadow-sm border border-border flex flex-col gap-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-secondary text-secondary-foreground flex items-center justify-center text-sm font-bold shrink-0">
                  2
                </div>
                <h3 className="font-semibold text-foreground">Analyse SSIM</h3>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Un score de similarité pixel par pixel est calculé pour chaque paire.
                Les fichiers sous le seuil sont signalés comme{' '}
                <strong className="text-foreground">non conformes</strong>.
              </p>
            </div>

            {/* Étape 3 */}
            <div className="relative z-10 bg-card rounded-xl p-6 shadow-sm border border-border flex flex-col gap-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-emerald-600 text-white flex items-center justify-center text-sm font-bold shrink-0">
                  3
                </div>
                <h3 className="font-semibold text-foreground">Approuvez & exportez</h3>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Comparez côte à côte, approuvez ou rejetez chaque fichier, ajoutez des commentaires.
                Rapport CSV exportable, historique automatique.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Zone de travail */}
      <div id="vos-fichiers" className="flex-1 bg-background">
        <div className="max-w-6xl mx-auto px-8 py-12">

          {/* Label section avec séparateurs */}
          <div className="flex items-center gap-3 mb-10">
            <div className="h-px flex-1 bg-border" />
            <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground px-2">
              Vos fichiers
            </p>
            <div className="h-px flex-1 bg-border" />
          </div>

          {/* Drop zones */}
          <div className="grid md:grid-cols-2 gap-10 mb-12">
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

          {/* Panneau d'analyse */}
          <Card className="max-w-lg mx-auto p-6 bg-muted/20 border border-border shadow-sm">
            <div className="space-y-5">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <label className="text-sm font-semibold text-foreground">
                    Seuil de similarité
                  </label>
                  <span className="text-sm font-bold text-primary tabular-nums">{threshold}%</span>
                </div>
                <Slider
                  value={[threshold]}
                  onValueChange={(value) => setThreshold(value[0])}
                  min={50}
                  max={100}
                  step={1}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground mt-2">
                  Fichiers sous ce seuil signalés comme non conformes.
                </p>
              </div>

              <div className="h-px bg-border" />

              <div className="text-center space-y-2">
                <Button
                  size="lg"
                  disabled={!canStartAnalysis || isAnalyzing}
                  onClick={handleStartAnalysis}
                  className="w-full py-6 text-base font-semibold tracking-wide"
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
                  <p className="text-xs text-muted-foreground">
                    {originalFiles.length} original{originalFiles.length > 1 ? 'x' : ''}
                    {' · '}
                    {printerFiles.length} imprimeur{printerFiles.length > 1 ? 's' : ''}
                  </p>
                )}
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Footer */}
      <footer className="py-4 text-center text-sm text-muted-foreground border-t">
        <p>ProofsLab v1.3.0 • PDF Comparison Laboratory</p>
      </footer>
    </main>
  );
}
