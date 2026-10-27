import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { AuthUser } from "@/api/auth";
import App from "@/App";

const mocks = vi.hoisted(() => ({
  login: vi.fn(),
  fetchMe: vi.fn(),
  logout: vi.fn(),
  changePassword: vi.fn(),
  listUsers: vi.fn(),
  getToken: vi.fn(),
}));

vi.mock("@/api/auth", () => ({
  login: mocks.login,
  fetchMe: mocks.fetchMe,
  logout: mocks.logout,
  changePassword: mocks.changePassword,
  listUsers: mocks.listUsers,
}));

vi.mock("@/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/api/client")>("@/api/client");
  return {
    ...actual,
    getToken: mocks.getToken,
    setToken: vi.fn(),
    clearToken: vi.fn(),
    setUnauthorizedHandler: vi.fn(),
  };
});

const salesUser: AuthUser = {
  id: "00000000-0000-4000-8000-000000000001",
  email: "sales@example.test",
  role: "sales",
  is_active: true,
  must_change_password: false,
  created_at: "2026-10-27T09:00:00Z",
};

const adminUser: AuthUser = { ...salesUser, role: "admin", email: "admin@example.test" };

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

describe("authentication", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.getToken.mockReturnValue(null);
  });

  it("sends an anonymous visitor to the login page", async () => {
    renderAt("/leads");

    expect(await screen.findByRole("heading", { name: "Sign in" }, { timeout: 5000 })).toBeTruthy();
  });

  it("signs in and lands on the lead desk", async () => {
    mocks.login.mockResolvedValue({
      access_token: "token",
      token_type: "bearer",
      user: salesUser,
    });

    renderAt("/login");

    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "sales@example.test" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "a-good-password" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("heading", { name: "Leads" }, { timeout: 5000 })).toBeTruthy();
    expect(mocks.login).toHaveBeenCalledWith("sales@example.test", "a-good-password");
  });

  it("shows the server's message for bad credentials", async () => {
    mocks.login.mockRejectedValue(new Error("Invalid email or password."));

    renderAt("/login");
    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "sales@example.test" },
    });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "wrong" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    const alert = await screen.findByRole("alert", {}, { timeout: 5000 });
    expect(alert.textContent).toBe("Invalid email or password.");
  });

  it("blocks a sales user from the admin screen", async () => {
    mocks.getToken.mockReturnValue("token");
    mocks.fetchMe.mockResolvedValue(salesUser);

    renderAt("/admin/users");

    expect(await screen.findByText("Administrators only", {}, { timeout: 5000 })).toBeTruthy();
  });

  it("lets an admin open the users screen", async () => {
    mocks.getToken.mockReturnValue("token");
    mocks.fetchMe.mockResolvedValue(adminUser);
    mocks.listUsers.mockResolvedValue([adminUser, salesUser]);

    renderAt("/admin/users");

    expect(await screen.findByRole("heading", { name: "Team" }, { timeout: 5000 })).toBeTruthy();
    expect(await screen.findByText("sales@example.test", {}, { timeout: 5000 })).toBeTruthy();
  });

  it("forces a temporary-password account to choose a new password", async () => {
    mocks.getToken.mockReturnValue("token");
    mocks.fetchMe.mockResolvedValue({ ...adminUser, must_change_password: true });

    renderAt("/leads");

    expect(await screen.findByRole("heading", { name: "Choose your password" }, { timeout: 5000 })).toBeTruthy();
  });
});
