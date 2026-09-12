import { auth } from "./firebase";

/**
 * Central API client for AcademiaLINK.
 * Communicates with the FastAPI backend with Firebase ID Bearer token.
 */
export const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

export async function getAuthHeaders(): Promise<Record<string, string>> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  try {
    // On a hard page reload, Firebase restores the persisted session asynchronously.
    // Without waiting here, the very first request(s) after reload fire while
    // auth.currentUser is still null, get sent with no Authorization header, and are
    // wrongly rejected by the backend with 401 - even though the user IS logged in.
    // authStateReady() resolves once that initial restoration has completed.
    await auth.authStateReady();
    const user = auth.currentUser;
    if (user) {
      const token = await user.getIdToken();
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
    }
  } catch (err) {
    console.warn("Could not retrieve Firebase ID token:", err);
  }
  return headers;
}

export async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const authHeaders = await getAuthHeaders();
  if (options.body instanceof FormData) {
    delete authHeaders["Content-Type"];
  }
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const url = `${API_BASE_URL}${cleanEndpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      ...authHeaders,
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    const errData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errData.detail || `API error ${response.status}`);
  }

  return response.json();
}

export function simulate<T>(data: T, delay = 300): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(structuredClone(data)), delay));
}

