import { apiClient } from "./api";

const STAFF_SESSION_KEY = "staff_session";

export interface StaffSession {
  accessToken: string;
  refreshToken: string;
  userId: number;
  username: string;
  role: string;
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  const parts = token.split(".");
  if (parts.length < 2) {
    return null;
  }

  try {
    const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padding = "=".repeat((4 - (base64.length % 4)) % 4);
    return JSON.parse(atob(`${base64}${padding}`));
  } catch {
    return null;
  }
}

export function getStaffSession(): StaffSession | null {
  if (typeof window === "undefined") {
    return null;
  }

  const stored = window.localStorage.getItem(STAFF_SESSION_KEY);
  if (!stored) {
    return null;
  }

  try {
    return JSON.parse(stored) as StaffSession;
  } catch {
    window.localStorage.removeItem(STAFF_SESSION_KEY);
    return null;
  }
}

export function getStaffToken(): string | null {
  return getStaffSession()?.accessToken || null;
}

export function getStaffAuthHeaders() {
  const token = getStaffToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export function getStaffUserId(): number | null {
  return getStaffSession()?.userId ?? null;
}

export function isStaffAuthenticated(): boolean {
  return !!getStaffSession();
}

export function saveStaffSession(session: StaffSession) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(STAFF_SESSION_KEY, JSON.stringify(session));
}

export function clearStaffSession() {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(STAFF_SESSION_KEY);
}

export async function loginStaff(username: string, password: string) {
  const response = await apiClient.post("/api/auth/auth/token/", {
    username,
    password,
    role: "staff",
  });

  const payload = response.data as {
    access: string;
    refresh: string;
    user_id: number;
    username?: string;
    role?: string;
  };

  const decoded = decodeJwtPayload(payload.access) as
    | {
        user_id?: number;
        username?: string;
        role?: string;
      }
    | null;

  const session: StaffSession = {
    accessToken: payload.access,
    refreshToken: payload.refresh,
    userId: payload.user_id ?? decoded?.user_id ?? 0,
    username: payload.username ?? decoded?.username ?? username,
    role: payload.role ?? decoded?.role ?? "staff",
  };

  saveStaffSession(session);
  return session;
}

export function logoutStaff() {
  clearStaffSession();
}