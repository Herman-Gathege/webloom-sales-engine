import { Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider, RequireAdmin, RequireAuth } from "@/auth/AuthProvider";
import { AppLayout } from "@/components/layout/AppLayout";
import { AccessDenied } from "@/routes/AccessDenied";
import { AdminUsers } from "@/routes/AdminUsers";
import { ChangePassword } from "@/routes/ChangePassword";
import { LeadDetail } from "@/routes/LeadDetail";
import { LeadImport } from "@/routes/LeadImport";
import { LeadList } from "@/routes/LeadList";
import { Login } from "@/routes/Login";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Public */}
        <Route path="login" element={<Login />} />

        {/* Signed in, but outside the shell: the forced first password change. */}
        <Route
          path="change-password"
          element={
            <RequireAuth>
              <ChangePassword />
            </RequireAuth>
          }
        />

        {/* Everything else needs a session. */}
        <Route
          element={
            <RequireAuth>
              <AppLayout />
            </RequireAuth>
          }
        >
          <Route index element={<Navigate to="/leads" replace />} />
          <Route path="leads" element={<LeadList />} />
          <Route path="leads/import" element={<LeadImport />} />
          <Route path="leads/:id" element={<LeadDetail />} />
          <Route
            path="admin/users"
            element={
              <RequireAdmin>
                <AdminUsers />
              </RequireAdmin>
            }
          />
          <Route path="access-denied" element={<AccessDenied />} />
          <Route path="*" element={<Navigate to="/leads" replace />} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}
