import { initializeApp, getApps, getApp } from "firebase/app";
import { getAuth } from "firebase/auth";

/**
 * Official AcademiaLINK Firebase Web configuration.
 */
export const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "academialink-b10b3.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "academialink-b10b3",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "academialink-b10b3.firebasestorage.app",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "951064475784",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:951064475784:web:c0c9b7ed37e065451e073d",
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || "G-MWKCWBC0BE",
};

// Initialize Firebase App singleton
export const app = !getApps().length ? initializeApp(firebaseConfig) : getApp();
export const auth = getAuth(app);
