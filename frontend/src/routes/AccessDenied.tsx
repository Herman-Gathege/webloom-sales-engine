import { Link } from "react-router-dom";

import { Scout } from "@/components/Scout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function AccessDenied() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Administrators only</CardTitle>
        <CardDescription>
          Your account is a sales account, so this screen is out of reach.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex items-center gap-4">
        <Scout size={64} mood="idle" />
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">
            Ask Herman or Mark if you need administrator access.
          </p>
          <Button asChild size="sm">
            <Link to="/leads">Back to the lead desk</Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
