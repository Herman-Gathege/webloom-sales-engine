"""Everything under /api/v1."""

from fastapi import APIRouter, Depends

from app.api.v1 import auth, health, leads, users
from app.auth import require_password_current

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
# Administrators only: the route itself also depends on `require_admin`, this
# keeps the prefix honest at a glance.
api_router.include_router(users.router)
# Every lead endpoint, including import and compliance review, needs a signed-in
# user. `health` and `auth` above stay public.
api_router.include_router(leads.router, dependencies=[Depends(require_password_current)])
