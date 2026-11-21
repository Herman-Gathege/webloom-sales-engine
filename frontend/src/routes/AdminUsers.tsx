import { useEffect, useState } from "react";

import { createUser, listUsers, resetUserPassword, updateUser, type AuthUser, type TemporaryPasswordResponse } from "@/api/auth";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
// no label component
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useMediaQuery } from "@/lib/use-media-query";

export function AdminUsers() {
  const [users, setUsers] = useState<AuthUser[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [temp, setTemp] = useState<TemporaryPasswordResponse | null>(null);
  const [creating, setCreating] = useState(false);
  const [newEmail, setNewEmail] = useState("");
  const [newRole, setNewRole] = useState<"admin" | "sales">("sales");
  const [busyId, setBusyId] = useState<string | null>(null);
  const showUserTable = useMediaQuery("(min-width: 768px)");

  async function refresh() {
    const rows = await listUsers();
    setUsers(rows);
  }

  useEffect(() => {
    let cancelled = false;
    listUsers()
      .then((rows) => {
        if (!cancelled) setUsers(rows);
      })
      .catch((cause: unknown) => {
        if (!cancelled) setError(cause instanceof Error ? cause.message : "Could not load users.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    setError(null);
    try {
      const res = await createUser(newEmail, newRole);
      setTemp(res);
      setNewEmail("");
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not create user.");
    } finally {
      setCreating(false);
    }
  }

  async function handleToggleActive(user: AuthUser) {
    setBusyId(user.id);
    try {
      await updateUser(user.id, { is_active: !user.is_active });
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not update user.");
    } finally {
      setBusyId(null);
    }
  }

  async function handleReset(user: AuthUser) {
    setBusyId(user.id);
    try {
      const res = await resetUserPassword(user.id);
      setTemp(res);
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not reset password.");
    } finally {
      setBusyId(null);
    }
  }

  async function handleRole(user: AuthUser, role: "admin" | "sales") {
    setBusyId(user.id);
    try {
      await updateUser(user.id, { role });
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not update role.");
    } finally {
      setBusyId(null);
    }
  }

  async function copyTemp() {
    if (!temp) return;
    await navigator.clipboard.writeText(temp.temporary_password);
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Team</CardTitle>
          <CardDescription>Manage accounts, roles, and password resets.</CardDescription>
        </div>
        <Dialog>
          <DialogTrigger asChild>
            <Button size="sm">Create user</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create user</DialogTitle>
              <DialogDescription>A temporary password will be issued once.</DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium">Email</label>
                <Input id="email" type="email" value={newEmail} onChange={(e) => setNewEmail(e.target.value)} required />
              </div>
              <div className="space-y-2">
                <label htmlFor="role" className="text-sm font-medium">Role</label>
                <select id="role" className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={newRole} onChange={(e) => setNewRole(e.target.value as "admin" | "sales")}>
                  <option value="sales">sales</option>
                  <option value="admin">admin</option>
                </select>
              </div>
              <DialogFooter>
                <Button type="submit" disabled={creating}>{creating ? "Creating…" : "Create"}</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <p role="alert" className="text-sm text-destructive">{error}</p>}

        {temp && (
          <div className="rounded-md border border-border bg-muted/40 p-3">
            <p className="text-sm font-medium">Temporary password (shown once)</p>
            <div className="mt-2 flex items-center gap-2">
              <code className="flex-1 break-all rounded bg-background px-2 py-1 text-sm">{temp.temporary_password}</code>
              <Button size="sm" variant="outline" onClick={copyTemp}>Copy</Button>
            </div>
            <p className="mt-2 text-xs text-muted-foreground">{temp.user.email} must change password on first sign-in.</p>
            <Button size="sm" variant="ghost" className="mt-2" onClick={() => setTemp(null)}>Dismiss</Button>
          </div>
        )}

        {!error && !users && (
          <div className="space-y-2">
            {Array.from({ length: 4 }).map((_, index) => (
              <Skeleton key={index} className="h-10 w-full" />
            ))}
          </div>
        )}

        {!error && users && (
          <>
            {!showUserTable && (
              <ul className="space-y-2">
                {users.map((user) => (
                  <li key={user.id} className="rounded-xl border border-border bg-card p-3">
                    <div className="flex items-start justify-between gap-3">
                      <p className="min-w-0 break-all font-medium">{user.email}</p>
                      <Badge variant="outline">{user.role}</Badge>
                    </div>
                    <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-border pt-3 text-xs text-muted-foreground">
                      <span>{user.is_active ? "Active" : "Disabled"}</span>
                      <span>{user.must_change_password ? "Temporary — must change" : "Password set by user"}</span>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Button size="sm" variant="outline" disabled={busyId === user.id} onClick={() => handleRole(user, user.role === "admin" ? "sales" : "admin")}>Toggle role</Button>
                      <Button size="sm" variant="outline" disabled={busyId === user.id} onClick={() => handleToggleActive(user)}>{user.is_active ? "Deactivate" : "Reactivate"}</Button>
                      <Button size="sm" variant="outline" disabled={busyId === user.id} onClick={() => handleReset(user)}>Reset password</Button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
            {showUserTable && (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Email</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Password</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell className="max-w-[16rem] break-all font-medium">{user.email}</TableCell>
                      <TableCell><Badge variant="outline">{user.role}</Badge></TableCell>
                      <TableCell className="text-sm">{user.is_active ? "Active" : "Disabled"}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">{user.must_change_password ? "Temporary — must change" : "Set by the user"}</TableCell>
                      <TableCell className="space-x-2">
                        <Button size="sm" variant="outline" disabled={busyId === user.id} onClick={() => handleRole(user, user.role === "admin" ? "sales" : "admin")}>Role</Button>
                        <Button size="sm" variant="outline" disabled={busyId === user.id} onClick={() => handleToggleActive(user)}>{user.is_active ? "Deactivate" : "Reactivate"}</Button>
                        <Button size="sm" variant="outline" disabled={busyId === user.id} onClick={() => handleReset(user)}>Reset</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
