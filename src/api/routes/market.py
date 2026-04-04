from fastapi import APIRouter

from src.data.market_data import get_earnings_calendar, get_options_chain, get_stock_price

router = APIRouter(prefix="/api/market", tags=["Market Data"])

@router.get("/price/{ticker}")
async def get_price(ticker: str):
    return get_stock_price(ticker)

@router.get("/options/{ticker}")
async def get_options(ticker: str):
    return get_options_chain(ticker)

@router.get("/earnings/{ticker}")
async def get_earnings(ticker: str):
    return get_earnings_calendar([ticker])
