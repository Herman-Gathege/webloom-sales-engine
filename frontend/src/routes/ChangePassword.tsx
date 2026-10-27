import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "@/auth/context";
import { Scout } from "@/components/Scout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export function ChangePassword() {
  const { user, changePassword, logout } = useAuth();
  const navigate = useNavigate();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const forced = user?.must_change_password ?? false;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (newPassword.length < 8) {
      setError("Use at least 8 characters for the new password.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("The two new passwords do not match.");
      return;
    }
    if (newPassword === currentPassword) {
      setError("Choose a password you have not used here before.");
      return;
    }

    setSubmitting(true);
    try {
      await changePassword(currentPassword, newPassword);
      navigate("/leads", { replace: true });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not change the password.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="grid min-h-screen place-items-center bg-background px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center gap-3 text-center">
          <Scout size={72} />
          <p className="text-[10px] uppercase tracking-[0.24em] text-muted-foreground">
            wadi · sales scout
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>{forced ? "Choose your password" : "Change password"}</CardTitle>
            <CardDescription>
              {forced
                ? "Your account was set up with a temporary password. Set your own before continuing."
                : "Set a new password for your account."}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4" noValidate>
              <div className="space-y-1.5">
                <label htmlFor="current" className="text-sm font-medium">
                  Current password
                </label>
                <Input
                  id="current"
                  type="password"
                  autoComplete="current-password"
                  autoFocus
                  value={currentPassword}
                  onChange={(event) => setCurrentPassword(event.target.value)}
                  disabled={submitting}
                />
              </div>

              <div className="space-y-1.5">
                <label htmlFor="new" className="text-sm font-medium">
                  New password
                </label>
                <Input
                  id="new"
                  type="password"
                  autoComplete="new-password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                  disabled={submitting}
                />
              </div>

              <div className="space-y-1.5">
                <label htmlFor="confirm" className="text-sm font-medium">
                  Confirm new password
                </label>
                <Input
                  id="confirm"
                  type="password"
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  disabled={submitting}
                />
              </div>

              {error && (
                <p role="alert" className="text-sm text-destructive">
                  {error}
                </p>
              )}

              <Button type="submit" className="w-full" disabled={submitting}>
                {submitting ? "Saving…" : "Set password"}
              </Button>

              <Button
                type="button"
                variant="ghost"
                className="w-full"
                onClick={() => void logout()}
                disabled={submitting}
              >
                Sign out instead
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
