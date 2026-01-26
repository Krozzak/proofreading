'use client';

import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';

interface SimilarityBarProps {
  score: number | null; // 0-100, null for loading state
  threshold: number; // 0-100
  showThreshold?: boolean;
  size?: 'sm' | 'md' | 'lg';
  isCalculating?: boolean;
}

export function SimilarityBar({
  score,
  threshold,
  showThreshold = true,
  size = 'md',
  isCalculating = false,
}: SimilarityBarProps) {
  const [displayProgress, setDisplayProgress] = useState(0);
  const [showResult, setShowResult] = useState(false);
  const isAboveThreshold = score !== null && score >= threshold;

  const heights = {
    sm: 'h-5',
    md: 'h-8',
    lg: 'h-10',
  };

  const textSizes = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  // Animate progress during calculation
  useEffect(() => {
    if (isCalculating) {
      setShowResult(false);
      setDisplayProgress(0);

      // Animate from 0 to 50% over 10 seconds
      const startTime = Date.now();
      const duration = 10000; // 10 seconds
      const targetProgress = 50;

      const animate = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min((elapsed / duration) * targetProgress, targetProgress);
        setDisplayProgress(progress);

        if (elapsed < duration && isCalculating) {
          requestAnimationFrame(animate);
        }
      };

      const animationId = requestAnimationFrame(animate);
      return () => cancelAnimationFrame(animationId);
    } else if (score !== null) {
      // Calculation finished - animate to final score
      setDisplayProgress(score);
      // Show result text after transition completes
      setTimeout(() => setShowResult(true), 700);
    }
  }, [isCalculating, score]);

  return (
    <div
      className={cn(
        'relative w-full bg-muted rounded-full overflow-hidden',
        heights[size]
      )}
    >
      {/* Progress bar */}
      <div
        className={cn(
          'absolute inset-y-0 left-0 rounded-full transition-all duration-700 ease-out',
          isCalculating
            ? 'bg-primary/60'
            : isAboveThreshold
              ? 'bg-green-500'
              : 'bg-red-500'
        )}
        style={{ width: `${Math.min(100, Math.max(0, displayProgress))}%` }}
      />

      {/* Threshold line */}
      {showThreshold && (
        <div
          className="absolute inset-y-0 w-0.5 bg-yellow-500 z-10"
          style={{ left: `${threshold}%` }}
        />
      )}

      {/* Text content */}
      <div
        className={cn(
          'absolute inset-0 flex items-center justify-center font-bold',
          textSizes[size],
          isCalculating
            ? 'text-white'
            : (displayProgress > 30)
              ? 'text-white'
              : 'text-foreground'
        )}
      >
        {isCalculating ? (
          <span className="flex items-center gap-2">
            <span className="animate-spin">⏳</span>
            Calcul en cours...
          </span>
        ) : showResult && score !== null ? (
          <span className="flex items-center gap-2">
            {Math.round(score)}%
            <span className={cn(
              'px-2 py-0.5 rounded text-xs font-bold',
              isAboveThreshold ? 'bg-white/20' : 'bg-white/20'
            )}>
              {isAboveThreshold ? '✓ CONFORME' : '✗ NON CONFORME'}
            </span>
          </span>
        ) : score !== null ? (
          <span>{Math.round(displayProgress)}%</span>
        ) : null}
      </div>
    </div>
  );
}
