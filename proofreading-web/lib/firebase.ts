/**
 * Firebase Client SDK configuration.
 * Used for authentication on the frontend.
 *
 * IMPORTANT: Firebase is only initialized on the client side.
 * During SSR/build, these exports will be undefined.
 */

import { initializeApp, getApps, FirebaseApp } from 'firebase/app';
import { getAuth, Auth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
};

// Only initialize Firebase on the client side
let app: FirebaseApp | undefined;
let auth: Auth | undefined;

if (typeof window !== 'undefined') {
  // Client-side only
  if (getApps().length === 0) {
    app = initializeApp(firebaseConfig);
  } else {
    app = getApps()[0];
  }
  auth = getAuth(app);
}

export { app, auth };
