'use client';

import { useEffect, useState, useRef } from 'react';
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
  const animationRef = useRef<number | null>(null);
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

  // Animate progress during calculation and to final value
  useEffect(() => {
    // Cancel any existing animation
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }

    if (isCalculating) {
      setShowResult(false);

      // Smooth indeterminate animation: oscillate between 20-80%
      const startTime = Date.now();
      const animate = () => {
        const elapsed = Date.now() - startTime;
        // Use sine wave for smooth back-and-forth motion
        // Completes one cycle every 2 seconds
        const cycle = (elapsed % 2000) / 2000;
        const progress = 20 + Math.sin(cycle * Math.PI * 2) * 30 + 30; // Range: 20-80%
        setDisplayProgress(progress);

        animationRef.current = requestAnimationFrame(animate);
      };

      animationRef.current = requestAnimationFrame(animate);
    } else if (score !== null) {
      // Calculation finished - smoothly animate from current position to final score
      const startProgress = displayProgress;
      const targetProgress = score;
      const startTime = Date.now();
      const duration = 500; // 500ms for final animation

      const animateToFinal = () => {
        const elapsed = Date.now() - startTime;
        const t = Math.min(elapsed / duration, 1);
        // Ease-out cubic for smooth deceleration
        const eased = 1 - Math.pow(1 - t, 3);
        const progress = startProgress + (targetProgress - startProgress) * eased;
        setDisplayProgress(progress);

        if (t < 1) {
          animationRef.current = requestAnimationFrame(animateToFinal);
        } else {
          setDisplayProgress(score);
          setShowResult(true);
        }
      };

      animationRef.current = requestAnimationFrame(animateToFinal);
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
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

      {/* Text content - always use text-shadow for readability */}
      <div
        className={cn(
          'absolute inset-0 flex items-center justify-center font-bold',
          textSizes[size]
        )}
        style={{
          color: '#ffffff',
          textShadow: '0 1px 2px rgba(0,0,0,0.5), 0 0 4px rgba(0,0,0,0.3)',
        }}
      >
        {isCalculating ? (
          <span className="flex items-center gap-2">
            <span className="animate-spin">⏳</span>
            Calcul en cours...
          </span>
        ) : showResult && score !== null ? (
          <span className="flex items-center gap-2">
            {Math.round(score)}%
            <span
              className="px-2 py-0.5 rounded text-xs font-bold"
              style={{
                backgroundColor: 'rgba(0,0,0,0.25)',
              }}
            >
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
