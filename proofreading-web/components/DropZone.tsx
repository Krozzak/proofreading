'use client';

import { useCallback, useState } from 'react';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface DropZoneProps {
  title: string;
  description: string;
  accentColor: 'primary' | 'secondary';
  files: File[];
  onFilesChange: (files: File[]) => void;
  accept?: string;
}

export function DropZone({
  title,
  description,
  accentColor,
  files,
  onFilesChange,
  accept = '.pdf',
}: DropZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const processFiles = useCallback(
    async (items: DataTransferItemList | FileList) => {
      const newFiles: File[] = [];

      // Handle DataTransferItemList (drag & drop)
      if ('length' in items && items[0] && 'webkitGetAsEntry' in items[0]) {
        const entries: FileSystemEntry[] = [];
        for (let i = 0; i < items.length; i++) {
          const entry = (items[i] as DataTransferItem).webkitGetAsEntry();
          if (entry) entries.push(entry);
        }

        const readEntry = async (entry: FileSystemEntry): Promise<File[]> => {
          if (entry.isFile) {
            return new Promise((resolve) => {
              (entry as FileSystemFileEntry).file((file) => {
                if (file.name.toLowerCase().endsWith('.pdf')) {
                  resolve([file]);
                } else {
                  resolve([]);
                }
              });
            });
          } else if (entry.isDirectory) {
            const dirReader = (entry as FileSystemDirectoryEntry).createReader();
            return new Promise((resolve) => {
              dirReader.readEntries(async (entries) => {
                const files: File[] = [];
                for (const e of entries) {
                  const subFiles = await readEntry(e);
                  files.push(...subFiles);
                }
                resolve(files);
              });
            });
          }
          return [];
        };

        for (const entry of entries) {
          const entryFiles = await readEntry(entry);
          newFiles.push(...entryFiles);
        }
      } else {
        // Handle FileList (input click)
        for (let i = 0; i < items.length; i++) {
          const file = items[i] as File;
          if (file.name.toLowerCase().endsWith('.pdf')) {
            newFiles.push(file);
          }
        }
      }

      if (newFiles.length > 0) {
        onFilesChange([...files, ...newFiles]);
      }
    },
    [files, onFilesChange]
  );

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragOver(false);

      if (e.dataTransfer.items) {
        await processFiles(e.dataTransfer.items);
      }
    },
    [processFiles]
  );

  const handleInputChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) {
        await processFiles(e.target.files);
      }
    },
    [processFiles]
  );

  const handleClick = useCallback(() => {
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    input.accept = accept;
    (input as HTMLInputElement & { webkitdirectory: boolean }).webkitdirectory = true;
    input.onchange = (e) => {
      const target = e.target as HTMLInputElement;
      if (target.files) {
        processFiles(target.files);
      }
    };
    input.click();
  }, [accept, processFiles]);

  const clearFiles = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      onFilesChange([]);
    },
    [onFilesChange]
  );

  const hasFiles = files.length > 0;

  return (
    <Card
      className={cn(
        'relative flex flex-col items-center justify-center p-8 cursor-pointer transition-all duration-300 border-2 border-dashed min-h-[280px]',
        isDragOver && 'scale-[1.02] shadow-lg',
        hasFiles ? 'border-solid' : 'border-dashed',
        accentColor === 'primary'
          ? isDragOver
            ? 'border-primary bg-primary/5'
            : hasFiles
            ? 'border-primary/50 bg-primary/5'
            : 'border-muted-foreground/25 hover:border-primary/50'
          : isDragOver
          ? 'border-secondary bg-secondary/5'
          : hasFiles
          ? 'border-secondary/50 bg-secondary/5'
          : 'border-muted-foreground/25 hover:border-secondary/50'
      )}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      {/* Header badge */}
      <div
        className={cn(
          'absolute top-0 left-0 right-0 py-2 px-4 text-center text-white font-semibold rounded-t-lg',
          accentColor === 'primary' ? 'bg-primary' : 'bg-secondary'
        )}
      >
        {title}
      </div>

      {/* Content */}
      <div className="mt-8 flex flex-col items-center gap-4 text-center">
        {hasFiles ? (
          <>
            <div className="text-5xl">✓</div>
            <div className="space-y-1">
              <p className="text-lg font-medium text-foreground">
                {files.length} fichier{files.length > 1 ? 's' : ''} PDF
              </p>
              <p className="text-sm text-muted-foreground">
                Cliquez pour ajouter plus de fichiers
              </p>
            </div>
            <button
              onClick={clearFiles}
              className="text-sm text-destructive hover:underline"
            >
              Effacer tout
            </button>
          </>
        ) : (
          <>
            <div className="text-5xl opacity-50">📁</div>
            <div className="space-y-1">
              <p className="text-lg font-medium text-foreground">{description}</p>
              <p className="text-sm text-muted-foreground">
                Glissez un dossier ici ou cliquez pour sélectionner
              </p>
            </div>
          </>
        )}
      </div>
    </Card>
  );
}
