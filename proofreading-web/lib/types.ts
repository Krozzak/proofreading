// Types for the Proofreading Web App

export interface FileInfo {
  name: string;
  path: string;
  code: string; // 8-character code extracted from filename
}

export interface ComparisonPair {
  index: number;
  code: string;
  originalFile: FileInfo | null;
  printerFile: FileInfo | null;
  similarity: number | null;
  totalPagesOriginal: number;
  totalPagesPrinter: number;
  validation: ValidationStatus;
  pageValidations: Record<number, PageValidation>;
  comment: string;
  validatedAt: string | null;
}

export type ValidationStatus = 'pending' | 'approved' | 'rejected' | 'partial';

export interface PageValidation {
  status: 'approved' | 'rejected' | null;
  comment?: string;
}

export interface UploadState {
  originalFiles: File[];
  printerFiles: File[];
  isUploading: boolean;
  uploadProgress: number;
}

export interface CompareState {
  pairs: ComparisonPair[];
  currentIndex: number;
  currentPage: number;
  threshold: number;
  isLoading: boolean;
}

export interface ComparisonResult {
  originalImage: string | null; // base64
  printerImage: string | null; // base64
  similarity: number;
  bounds: ContentBounds | null;
  confidence: number;
  method: 'threshold' | 'edge' | 'full' | 'manual';
}

export interface ContentBounds {
  left: number;
  top: number;
  right: number;
  bottom: number;
}

export interface ExportRow {
  code: string;
  filename: string;
  matching: string;
  similarity: string;
  validation: string;
  comment: string;
  date: string;
}
