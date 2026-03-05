import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.database import get_session, init_db
from app.github import create_github_client, fetch_github_profile
from app.models import ProfileHistory

logger = logging.getLogger(__name__)


def _safe_url(url: str | None) -> str:
    """Return the URL only if it uses http/https scheme; otherwise return empty string."""
    if url and url.startswith(("https://", "http://")):
        return url
    return ""


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' https://avatars.githubusercontent.com; "
            "style-src 'self';"
        )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_db()
    logger.info("Database initialized.")
    async with create_github_client() as client:
        app.state.http_client = client
        yield


app = FastAPI(title="dotenvx-sample", lifespan=lifespan)
app.add_middleware(SecurityHeadersMiddleware)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
templates.env.filters["safe_url"] = _safe_url


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/profile/{username}", response_class=HTMLResponse)
async def profile(
    request: Request,
    username: str,
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    try:
        data = await fetch_github_profile(username, request.app.state.http_client)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="GitHub user not found")
        logger.error("GitHub API error for user %s: %s", username, exc)
        raise HTTPException(status_code=502, detail="GitHub API error")

    record = ProfileHistory(
        username=data.get("login", username),
        display_name=data.get("name"),
        avatar_url=data.get("avatar_url"),
        bio=data.get("bio"),
        public_repos=data.get("public_repos"),
        followers=data.get("followers"),
    )
    session.add(record)
    await session.commit()

    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "profile": data},
    )


@app.get("/history", response_class=HTMLResponse)
async def history(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    result = await session.execute(
        select(ProfileHistory).order_by(ProfileHistory.viewed_at.desc()).limit(50)
    )
    records = result.scalars().all()

    return templates.TemplateResponse(
        "history.html",
        {"request": request, "records": records},
    )
