import { Navigate } from "react-router-dom";

import { SessionLoading } from "@/auth/AuthProvider";
import { useAuth } from "@/auth/context";

/** Public overview before login; the static page also remains directly accessible. */
export function WorkflowLanding() {
  const { status, user } = useAuth();

  if (status === "loading") return <SessionLoading />;
  if (status === "authenticated" && user) {
    return <Navigate to={user.must_change_password ? "/change-password" : "/leads"} replace />;
  }

  return (
    <iframe
      src="/workflow.html"
      title="How Wadi works"
      className="h-dvh min-h-[40rem] w-full border-0 bg-background"
    />
  );
}
