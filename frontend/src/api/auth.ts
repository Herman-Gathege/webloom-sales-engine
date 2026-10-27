import { apiRequest, setToken } from "./client";

export type Role = "admin" | "sales";

export interface AuthUser {
  id: string;
  email: string;
  role: Role;
  is_active: boolean;
  must_change_password: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const response = await apiRequest<TokenResponse>("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  setToken(response.access_token);
  return response;
}

export async function fetchMe(): Promise<AuthUser> {
  return apiRequest<AuthUser>("/auth/me");
}

export async function logout(): Promise<void> {
  try {
    await apiRequest<void>("/auth/logout", { method: "POST" });
  } finally {
    // Even if the API is unreachable, the browser must forget the token.
    setToken(null);
  }
}

export async function changePassword(
  currentPassword: string,
  newPassword: string,
): Promise<TokenResponse> {
  const response = await apiRequest<TokenResponse>("/auth/change-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });
  setToken(response.access_token);
  return response;
}

export async function listUsers(): Promise<AuthUser[]> {
  return apiRequest<AuthUser[]>("/users");
}
