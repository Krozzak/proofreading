'use client';

/**
 * Authentication context provider using Firebase Auth.
 * Provides user state, quota info, and auth methods to the app.
 */

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  ReactNode,
} from 'react';
import {
  User,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut,
  sendPasswordResetEmail,
} from 'firebase/auth';
import { auth } from './firebase';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Quota information from the backend.
 */
export interface QuotaInfo {
  used: number;
  limit: number;
  remaining: number;
  resetsAt: string;
}

/**
 * Auth context type definition.
 */
interface AuthContextType {
  /** Current Firebase user (null if not logged in) */
  user: User | null;
  /** True while checking initial auth state */
  loading: boolean;
  /** Current quota info (null if not fetched) */
  quota: QuotaInfo | null;
  /** Sign in with email and password */
  signIn: (email: string, password: string) => Promise<void>;
  /** Create new account with email and password */
  signUp: (email: string, password: string) => Promise<void>;
  /** Sign out current user */
  signOut: () => Promise<void>;
  /** Send password reset email */
  resetPassword: (email: string) => Promise<void>;
  /** Get current ID token for API calls */
  getIdToken: () => Promise<string | null>;
  /** Refresh quota from backend */
  refreshQuota: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Auth provider component.
 * Wrap your app with this to provide auth context.
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [quota, setQuota] = useState<QuotaInfo | null>(null);

  /**
   * Get ID token for API calls.
   */
  const getIdToken = useCallback(async (): Promise<string | null> => {
    if (!user) return null;
    try {
      return await user.getIdToken();
    } catch {
      return null;
    }
  }, [user]);

  /**
   * Fetch quota from backend.
   */
  const refreshQuota = useCallback(async () => {
    const token = await getIdToken();
    if (!token) {
      setQuota(null);
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/quota`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setQuota(data);
      }
    } catch (error) {
      console.error('Failed to fetch quota:', error);
    }
  }, [getIdToken]);

  /**
   * Listen to auth state changes.
   */
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      setUser(firebaseUser);
      setLoading(false);

      if (firebaseUser) {
        // Fetch quota after login
        const token = await firebaseUser.getIdToken();
        try {
          const response = await fetch(`${API_URL}/api/quota`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (response.ok) {
            const data = await response.json();
            setQuota(data);
          }
        } catch {
          // Quota fetch failed, not critical
        }
      } else {
        setQuota(null);
      }
    });

    return unsubscribe;
  }, []);

  /**
   * Sign in with email and password.
   */
  const signIn = async (email: string, password: string) => {
    await signInWithEmailAndPassword(auth, email, password);
  };

  /**
   * Create new account.
   */
  const signUp = async (email: string, password: string) => {
    await createUserWithEmailAndPassword(auth, email, password);
  };

  /**
   * Sign out.
   */
  const signOut = async () => {
    await firebaseSignOut(auth);
    setQuota(null);
  };

  /**
   * Send password reset email.
   */
  const resetPassword = async (email: string) => {
    await sendPasswordResetEmail(auth, email);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        quota,
        signIn,
        signUp,
        signOut,
        resetPassword,
        getIdToken,
        refreshQuota,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook to access auth context.
 * Must be used within AuthProvider.
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
