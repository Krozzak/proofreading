'use client';

import { cn } from '@/lib/utils';

interface SimilarityBarProps {
  score: number; // 0-100
  threshold: number; // 0-100
  showThreshold?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function SimilarityBar({
  score,
  threshold,
  showThreshold = true,
  size = 'md',
}: SimilarityBarProps) {
  const isAboveThreshold = score >= threshold;

  const heights = {
    sm: 'h-4',
    md: 'h-7',
    lg: 'h-10',
  };

  const textSizes = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  return (
    <div className="w-full space-y-1">
      <div
        className={cn(
          'relative w-full bg-muted rounded-full overflow-hidden',
          heights[size]
        )}
      >
        {/* Progress bar */}
        <div
          className={cn(
            'absolute inset-y-0 left-0 transition-all duration-500 ease-out rounded-full',
            isAboveThreshold ? 'bg-green-500' : 'bg-red-500'
          )}
          style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
        />

        {/* Threshold line */}
        {showThreshold && (
          <div
            className="absolute inset-y-0 w-0.5 bg-yellow-500 z-10"
            style={{ left: `${threshold}%` }}
          />
        )}

        {/* Score text */}
        <div
          className={cn(
            'absolute inset-0 flex items-center justify-center font-bold',
            textSizes[size],
            score > 30 ? 'text-white' : 'text-foreground'
          )}
        >
          {Math.round(score)}% {isAboveThreshold ? '✓' : '✗'}
        </div>
      </div>

      {/* Status label */}
      <div className="flex justify-between items-center text-xs">
        <span className={cn(
          'font-medium',
          isAboveThreshold ? 'text-green-600' : 'text-red-600'
        )}>
          {isAboveThreshold ? 'CONFORME' : 'NON CONFORME'}
        </span>
        {showThreshold && (
          <span className="text-muted-foreground">
            Seuil: {threshold}%
          </span>
        )}
      </div>
    </div>
  );
}
