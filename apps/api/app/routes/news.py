from fastapi import APIRouter

from app.services import news_service

router = APIRouter()


@router.get("/news")
def list_news():
    return news_service.fetch_espn_news()
