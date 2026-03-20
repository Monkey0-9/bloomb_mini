"""
SatTrade Options Chains via yfinance
"""
import structlog
import asyncio
from typing import Dict, Any

log = structlog.get_logger(__name__)

async def fetch_option_chains(ticker: str) -> Dict[str, Any]:
    try:
        import yfinance as yf
        loop = asyncio.get_event_loop()
        ticker_obj = yf.Ticker(ticker)
        
        # Get expirations
        expirations = await loop.run_in_executor(None, getattr, ticker_obj, 'options')
        if not expirations:
            return {"expirations": [], "chains": {}}
            
        # Just grab the closest expiration to be fast
        closest_exp = expirations[0]
        chain = await loop.run_in_executor(None, ticker_obj.option_chain, closest_exp)
        
        calls = chain.calls.to_dict(orient='records') if chain.calls is not None else []
        puts = chain.puts.to_dict(orient='records') if chain.puts is not None else []
        
        # JSON serialize
        def clean_df_records(records):
            return [{str(k): (str(v) if str(v) != 'nan' else None) for k, v in r.items()} for r in records]

        return {
            "expirations": expirations,
            "chains": {
                closest_exp: {
                    "calls": clean_df_records(calls),
                    "puts": clean_df_records(puts)
                }
            }
        }
    except Exception as exc:
        log.warning("options_fetch_failed", ticker=ticker, error=str(exc))
        return {"expirations": [], "chains": {}}
