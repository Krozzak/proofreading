'use client';

/**
 * Authentication modal for login, register, and password reset.
 */

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/lib/auth-context';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type AuthMode = 'login' | 'register' | 'reset';

/**
 * Get user-friendly error message from Firebase error code.
 */
function getErrorMessage(code: string): string {
  const messages: Record<string, string> = {
    'auth/email-already-in-use': 'Cet email est déjà utilisé',
    'auth/invalid-email': 'Email invalide',
    'auth/user-not-found': 'Aucun compte avec cet email',
    'auth/wrong-password': 'Mot de passe incorrect',
    'auth/weak-password': 'Mot de passe trop faible (min 6 caractères)',
    'auth/invalid-credential': 'Email ou mot de passe incorrect',
    'auth/too-many-requests': 'Trop de tentatives, réessayez plus tard',
  };
  return messages[code] || 'Une erreur est survenue';
}

export function AuthModal({ isOpen, onClose }: AuthModalProps) {
  const [mode, setMode] = useState<AuthMode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const { signIn, signUp, resetPassword } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);

    try {
      if (mode === 'login') {
        await signIn(email, password);
        onClose();
        resetForm();
      } else if (mode === 'register') {
        await signUp(email, password);
        onClose();
        resetForm();
      } else {
        await resetPassword(email);
        setMessage('Email de réinitialisation envoyé !');
      }
    } catch (err: unknown) {
      const firebaseError = err as { code?: string };
      setError(getErrorMessage(firebaseError.code || ''));
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setEmail('');
    setPassword('');
    setError('');
    setMessage('');
  };

  const switchMode = (newMode: AuthMode) => {
    setMode(newMode);
    setError('');
    setMessage('');
  };

  const getTitle = () => {
    switch (mode) {
      case 'login':
        return 'Connexion';
      case 'register':
        return 'Créer un compte';
      case 'reset':
        return 'Mot de passe oublié';
    }
  };

  const getButtonText = () => {
    if (loading) return 'Chargement...';
    switch (mode) {
      case 'login':
        return 'Se connecter';
      case 'register':
        return "S'inscrire";
      case 'reset':
        return 'Envoyer le lien';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{getTitle()}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium mb-1"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              placeholder="votre@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border rounded-md bg-background"
              required
              autoComplete="email"
            />
          </div>

          {mode !== 'reset' && (
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium mb-1"
              >
                Mot de passe
              </label>
              <input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 border rounded-md bg-background"
                required
                minLength={6}
                autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
              />
            </div>
          )}

          {error && (
            <p className="text-destructive text-sm bg-destructive/10 p-2 rounded">
              {error}
            </p>
          )}

          {message && (
            <p className="text-green-600 text-sm bg-green-50 p-2 rounded">
              {message}
            </p>
          )}

          <Button type="submit" className="w-full" disabled={loading}>
            {getButtonText()}
          </Button>
        </form>

        <div className="text-center text-sm text-muted-foreground pt-2 border-t">
          {mode === 'login' ? (
            <div className="space-y-1">
              <div>
                <span>Pas encore de compte ? </span>
                <button
                  type="button"
                  onClick={() => switchMode('register')}
                  className="text-primary hover:underline font-medium"
                >
                  Créer un compte
                </button>
              </div>
              <div>
                <button
                  type="button"
                  onClick={() => switchMode('reset')}
                  className="text-primary hover:underline"
                >
                  Mot de passe oublié ?
                </button>
              </div>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => switchMode('login')}
              className="text-primary hover:underline"
            >
              Retour à la connexion
            </button>
          )}
        </div>

        {mode === 'register' && (
          <p className="text-xs text-muted-foreground text-center">
            5 comparaisons/jour gratuites avec un compte
          </p>
        )}
      </DialogContent>
    </Dialog>
  );
}
