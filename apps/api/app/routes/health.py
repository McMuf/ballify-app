from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()


@router.get("/health")
def health():
    settings = get_settings()
    return {
        "status": "ok",
        "reddit_configured": settings.reddit_configured,
        "odds_configured": settings.odds_configured,
    }
