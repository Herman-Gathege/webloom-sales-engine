import { Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider, RequireAdmin, RequireAuth, SessionLoading } from "@/auth/AuthProvider";
import { useAuth } from "@/auth/context";
import { AppLayout } from "@/components/layout/AppLayout";
import { AccessDenied } from "@/routes/AccessDenied";
import { AdminUsers } from "@/routes/AdminUsers";
import { CampaignCreate } from "@/routes/CampaignCreate";
import { CampaignDetail } from "@/routes/CampaignDetail";
import { CampaignList } from "@/routes/CampaignList";
import { ChangePassword } from "@/routes/ChangePassword";
import { InternalOrientation } from "@/routes/InternalOrientation";
import { LandingPage } from "@/routes/LandingPage";
import { LeadDetail } from "@/routes/LeadDetail";
import { LeadImport } from "@/routes/LeadImport";
import { LeadList } from "@/routes/LeadList";
import { Login } from "@/routes/Login";
import { OfferCatalog } from "@/routes/OfferCatalog";
import { TemplateCatalog } from "@/routes/TemplateCatalog";
import { WorkflowPage } from "@/routes/WorkflowPage";

function LandingRoute() {
  const { status, user } = useAuth();

  if (status === "loading") return <SessionLoading />;
  if (status === "authenticated" && user) {
    return (
      <Navigate
        to={user.must_change_password ? "/change-password" : "/leads"}
        replace
      />
    );
  }
  return <LandingPage />;
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Public */}
        <Route index element={<LandingRoute />} />
        <Route path="workflow" element={<WorkflowPage />} />
        <Route path="workflow.html" element={<Navigate to="/workflow" replace />} />
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
          <Route path="leads" element={<LeadList />} />
          <Route path="app" element={<Navigate to="/leads" replace />} />
          <Route path="leads/import" element={<LeadImport />} />
          <Route path="leads/:id" element={<LeadDetail />} />
          <Route path="campaigns" element={<CampaignList />} />
          <Route path="campaigns/new" element={<CampaignCreate />} />
          <Route path="campaigns/:id/edit" element={<CampaignCreate />} />
          <Route path="campaigns/:id" element={<CampaignDetail />} />
          <Route path="catalog/offers" element={<OfferCatalog />} />
          <Route path="catalog/templates" element={<TemplateCatalog />} />
          <Route path="internal" element={<InternalOrientation />} />
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
