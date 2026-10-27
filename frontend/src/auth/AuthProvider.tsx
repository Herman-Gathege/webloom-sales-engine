import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { Navigate, useLocation } from "react-router-dom";

import * as authApi from "@/api/auth";
import type { AuthUser } from "@/api/auth";
import { clearToken, getToken, setUnauthorizedHandler } from "@/api/client";
import { AuthContext, useAuth, type AuthStatus } from "@/auth/context";
import { Scout } from "@/components/Scout";

export function AuthProvider({ children }: { children: ReactNode }) {
  // Start in "loading" only when there is a token to check; otherwise we know
  // the answer already and the login page can render immediately.
  const [status, setStatus] = useState<AuthStatus>(() =>
    getToken() ? "loading" : "anonymous",
  );
  const [user, setUser] = useState<AuthUser | null>(null);

  // Any 401 from anywhere in the app drops the session.
  useEffect(() => {
    setUnauthorizedHandler(() => {
      clearToken();
      setUser(null);
      setStatus("anonymous");
    });
    return () => setUnauthorizedHandler(null);
  }, []);

  // A page load with a stored token asks the API who it belongs to.
  useEffect(() => {
    if (!getToken()) return;
    let cancelled = false;

    authApi
      .fetchMe()
      .then((me) => {
        if (cancelled) return;
        setUser(me);
        setStatus("authenticated");
      })
      .catch(() => {
        if (cancelled) return;
        clearToken();
        setUser(null);
        setStatus("anonymous");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const response = await authApi.login(email, password);
    setUser(response.user);
    setStatus("authenticated");
    return response.user;
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      clearToken();
      setUser(null);
      setStatus("anonymous");
    }
  }, []);

  const changePassword = useCallback(async (currentPassword: string, newPassword: string) => {
    const response = await authApi.changePassword(currentPassword, newPassword);
    setUser(response.user);
    setStatus("authenticated");
  }, []);

  const value = useMemo(
    () => ({ status, user, login, logout, changePassword }),
    [status, user, login, logout, changePassword],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function SessionLoading() {
  return (
    <div className="grid min-h-screen place-items-center bg-background" role="status">
      <div className="flex flex-col items-center gap-3">
        <Scout size={64} mood="loading" />
        <p className="text-sm text-muted-foreground">Checking your session…</p>
      </div>
    </div>
  );
}

/**
 * Gate for every signed-in screen. Also enforces the first-login password
 * change: a bootstrapped account cannot reach the lead desk until it has set
 * its own password.
 */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { status, user } = useAuth();
  const location = useLocation();

  if (status === "loading") return <SessionLoading />;
  if (status === "anonymous" || !user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  if (user.must_change_password && location.pathname !== "/change-password") {
    return <Navigate to="/change-password" replace />;
  }
  return <>{children}</>;
}

/** Administrators only. Sales get a real page, not a redirect loop. */
export function RequireAdmin({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  if (user?.role !== "admin") return <Navigate to="/access-denied" replace />;
  return <>{children}</>;
}
