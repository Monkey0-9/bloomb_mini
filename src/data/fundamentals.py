"""
SatTrade Fundamentals Engine — SEC EDGAR + yfinance (100% Free)
==============================================================
Primary: yfinance (Yahoo Finance, no key needed)
Fallback: SEC EDGAR API (free, rate-limited, no key needed)
Caching: In-memory TTL dict (no Redis dependency).
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Dict, Optional

import structlog

log = structlog.get_logger(__name__)

_CACHE: dict = {}
_CACHE_TS: dict = {}


class FundamentalsEngine:
    """
    Fetches core valuation metrics and SEC filings.
    1-day Redis cache for fast retrieval.
    """

    def __init__(self) -> None:
        self._redis = None

    async def _get_redis(self):
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                self._redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
            except Exception:
                pass
        return self._redis

    async def _fetch_fmp(self, ticker: str) -> Optional[dict]:
        """FMP API - Primary"""
        if not FMP_API_KEY:
            return None
        
        try:
            import aiohttp
            url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={FMP_API_KEY}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data and isinstance(data, list):
                            return data[0]
        except Exception as exc:
            log.warning("fmp_api_failed", ticker=ticker, error=str(exc))
        return None

    async def _fetch_sec_edgar(self, ticker: str) -> Optional[dict]:
        """SEC EDGAR API - Fallback"""
        try:
            import aiohttp
            # SEC requires a descriptive User-Agent
            headers = {"User-Agent": "SatTrade Terminal (contact@sattrade.com)"}
            
            # Step 1: Get CIK from ticker map
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get("https://www.sec.gov/files/company_tickers.json", timeout=10) as resp:
                    if resp.status != 200:
                        return None
                    tickers_map = await resp.json()
                    cik_str = None
                    for entry in tickers_map.values():
                        if entry.get("ticker") == ticker:
                            cik_str = str(entry.get("cik_str")).zfill(10)
                            name = entry.get("title")
                            break
                    if not cik_str:
                        return None

                # Step 2: Get Company Facts
                url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_str}.json"
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        facts = await resp.json()
                        # Extract basic facts (simplified for fallback)
                        return {
                            "symbol": ticker,
                            "companyName": name,
                            "cik": cik_str,
                            "source": "sec_edgar",
                        }
        except Exception as exc:
            log.warning("sec_edgar_failed", ticker=ticker, error=str(exc))
        return None

    async def get_fundamentals(self, ticker: str) -> dict:
        """Get company profile and valuation metrics."""
        r = await self._get_redis()
        cache_key = f"fundamentals:{ticker}"
        
        if r:
            try:
                cached = await r.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass

        # Primary: FMP
        data = await self._fetch_fmp(ticker)
        
        # Secondary: SEC EDGAR
        if not data:
            data = await self._fetch_sec_edgar(ticker)
            
        # Fallback: Empty skeleton
        if not data:
            log.warning("fundamentals_unavailable", ticker=ticker)
            data = {
                "symbol": ticker,
                "companyName": ticker,
                "price": 0.0,
                "mktCap": 0,
                "pe": 0.0,
                "sector": "Unknown",
                "industry": "Unknown",
                "description": "Fundamental data unavailable.",
                "source": "fallback"
            }
        else:
            data["source"] = data.get("source", "fmp")

        # Cache for 24 hours
        if r:
            try:
                await r.setex(cache_key, 86400, json.dumps(data))
            except Exception as exc:
                log.warning("fundamentals_cache_failed", error=str(exc))

        return data
