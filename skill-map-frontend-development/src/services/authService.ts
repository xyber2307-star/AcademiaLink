import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  updateProfile,
  signOut,
} from "firebase/auth";
import type { User, UserRole } from "../types";
import { apiRequest } from "./api";
import { auth } from "./firebase";

const STORAGE_KEY = "skillmap.auth";

export interface LoginPayload {
  email: string;
  password: string;
  role: UserRole;
}

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
  role: UserRole;
  institution?: string;
}

export const authService = {
  async login(payload: LoginPayload): Promise<User> {
    // 1. Real Firebase Authentication with Email/Password
    const userCredential = await signInWithEmailAndPassword(auth, payload.email, payload.password);
    const fbUser = userCredential.user;

    // 2. Fetch authenticated profile from FastAPI backend via Bearer token
    const profile = await apiRequest<{
      uid: string;
      email: string;
      name: string;
      role: UserRole;
      avatar?: string;
      verified?: boolean;
    }>("/users/me");

    const user: User = {
      id: profile.uid || fbUser.uid,
      name: profile.name || fbUser.displayName || payload.email.split("@")[0],
      email: profile.email || fbUser.email || payload.email,
      role: profile.role || "student",
      avatar: profile.avatar || fbUser.photoURL || "https://i.pravatar.cc/150?img=47",
      verified: true,
    };

    localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
    return user;
  },

  async register(payload: RegisterPayload): Promise<User> {
    // 1. Create real user in Firebase Authentication
    const userCredential = await createUserWithEmailAndPassword(auth, payload.email, payload.password);
    const fbUser = userCredential.user;

    if (payload.name) {
      await updateProfile(fbUser, { displayName: payload.name });
    }

    // 2. Initialize and verify profile on FastAPI backend (PUT /api/users/me)
    const profile = await apiRequest<{
      uid: string;
      email: string;
      name: string;
      role: UserRole;
    }>("/users/me", {
      method: "PUT",
      body: JSON.stringify({
        name: payload.name,
        institution: payload.institution || "",
      }),
    });

    const user: User = {
      id: fbUser.uid,
      name: profile.name || payload.name,
      email: fbUser.email || payload.email,
      role: profile.role || "student",
      verified: true,
    };

    localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
    return user;
  },

  async loginWithGoogle(): Promise<User> {
    // 1. Real Firebase Authentication via Google popup
    const userCredential = await signInWithPopup(auth, new GoogleAuthProvider());
    const fbUser = userCredential.user;

    // 2. Fetch (or, on first sign-in, self-provision) the backend profile via Bearer token.
    // get_current_user() on the backend creates a default "student" profile the first
    // time a verified Firebase UID has no matching Firestore document, so this works
    // for both returning Google users and brand-new ones without a separate register step.
    const profile = await apiRequest<{
      uid: string;
      email: string;
      name: string;
      role: UserRole;
      avatar?: string;
      verified?: boolean;
    }>("/users/me");

    const user: User = {
      id: profile.uid || fbUser.uid,
      name: profile.name || fbUser.displayName || (fbUser.email || "").split("@")[0],
      email: profile.email || fbUser.email || "",
      role: profile.role || "student",
      avatar: profile.avatar || fbUser.photoURL || "https://i.pravatar.cc/150?img=47",
      verified: true,
    };

    localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
    return user;
  },

  async verifyEmail(_code: string): Promise<User | null> {
    const u = authService.getCurrentUser();
    if (!u) return null;
    const verified = { ...u, verified: true };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(verified));
    return verified;
  },

  logout() {
    try {
      signOut(auth);
    } catch (err) {
      console.warn("Error signing out of Firebase:", err);
    }
    localStorage.removeItem(STORAGE_KEY);
  },

  getCurrentUser(): User | null {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? (JSON.parse(raw) as User) : null;
    } catch {
      return null;
    }
  },
};

