"""
Price Chart Signal Overlay - Visualize satellite signals on financial charts.

Integrates satellite thermal anomaly signals with price data from yfinance,
showing anomaly_sigma as secondary Y-axis overlay with earnings date markers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


@dataclass
class ChartSignalPoint:
    """A signal point for chart overlay."""
    date: datetime
    anomaly_sigma: float
    signal_score: float  # 0-100
    frp_mw: float
    facility_name: str
    direction: str
    is_earnings_date: bool = False
    earnings_eps_estimate: float | None = None


@dataclass
class SignalOverlayChart:
    """Complete chart data with price and satellite signal overlay."""
    ticker: str
    company_name: str
    price_data: pd.DataFrame  # OHLCV
    signal_points: list[ChartSignalPoint]
    anomaly_axis_range: tuple[float, float]  # Min/max for secondary axis
    earnings_dates: list[dict[str, Any]]
    correlation_summary: dict[str, float]  # Signal-price correlation stats


class PriceSignalOverlay:
    """
    Creates price charts with satellite signal overlay.
    
    Features:
    - Fetches 90-day price history from yfinance (free, no API key)
    - Overlays thermal anomaly sigma as secondary Y-axis
    - Marks next earnings date with vertical line
    - Shows signal-to-price correlation
    - Returns data for Plotly/D3.js frontend rendering
    """

    def __init__(self):
        self._price_cache: dict[str, tuple[pd.DataFrame, datetime]] = {}
        self.cache_ttl = 300  # 5 minutes

    def fetch_price_history(self,
                           ticker: str,
                           days: int = 90) -> pd.DataFrame:
        """
        Fetch price history from yfinance with caching.
        
        Args:
            ticker: Stock ticker symbol
            days: Number of days of history
            
        Returns:
            DataFrame with OHLCV columns
        """
        cache_key = f"{ticker}_{days}d"
        now = datetime.now(UTC)

        # Check cache
        if cache_key in self._price_cache:
            df, ts = self._price_cache[cache_key]
            if (now - ts).total_seconds() < self.cache_ttl:
                return df

        try:
            # Download from yfinance
            end = now
            start = end - timedelta(days=days)

            df = yf.download(
                ticker,
                start=start.strftime('%Y-%m-%d'),
                end=end.strftime('%Y-%m-%d'),
                auto_adjust=True,
                progress=False
            )

            if df.empty:
                logger.warning(f"No price data for {ticker}")
                return pd.DataFrame()

            # Standardize columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Ensure standard column names
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })

            # Cache
            self._price_cache[cache_key] = (df, now)

            logger.info(f"Fetched {len(df)} days of price data for {ticker}")
            return df

        except Exception as e:
            logger.error(f"Price fetch failed for {ticker}: {e}")
            # Return cached if available
            if cache_key in self._price_cache:
                return self._price_cache[cache_key][0]
            return pd.DataFrame()

    def fetch_earnings_calendar(self, ticker: str) -> list[dict[str, Any]]:
        """
        Fetch upcoming earnings date for a ticker.
        
        Args:
            ticker: Stock ticker
            
        Returns:
            List of earnings events with dates and EPS estimates
        """
        try:
            stock = yf.Ticker(ticker)
            calendar = stock.calendar

            if calendar is None or calendar.empty:
                return []

            earnings = []
            # Handle both DataFrame and dict formats
            if isinstance(calendar, pd.DataFrame):
                for idx, row in calendar.iterrows():
                    earnings.append({
                        'date': idx if isinstance(idx, datetime) else row.get('Earnings Date'),
                        'eps_estimate': row.get('EPS Estimate'),
                        'eps_actual': row.get('Reported EPS'),
                    })
            else:
                earnings.append({
                    'date': calendar.get('Earnings Date'),
                    'eps_estimate': calendar.get('EPS Estimate'),
                })

            return earnings

        except Exception as e:
            logger.warning(f"Earnings calendar fetch failed for {ticker}: {e}")
            return []

    def get_company_info(self, ticker: str) -> dict[str, str]:
        """Get company name and info from yfinance."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return {
                'name': info.get('longName', ticker),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
            }
        except Exception:
            return {'name': ticker, 'sector': 'Unknown', 'industry': 'Unknown'}

    def create_signal_overlay(self,
                             ticker: str,
                             thermal_signals: list[Any],
                             days: int = 90) -> SignalOverlayChart:
        """
        Create price chart with satellite signal overlay.
        
        Args:
            ticker: Stock ticker
            thermal_signals: List of thermal signal objects for this ticker
            days: Days of price history to fetch
            
        Returns:
            SignalOverlayChart with all data for frontend rendering
        """
        # Fetch price data
        price_df = self.fetch_price_history(ticker, days)

        # Get company info
        company_info = self.get_company_info(ticker)

        # Fetch earnings dates
        earnings = self.fetch_earnings_calendar(ticker)

        # Filter signals for this ticker
        ticker_signals = [
            s for s in thermal_signals
            if hasattr(s, 'primary_ticker') and s.primary_ticker == ticker
        ]

        # Convert signals to chart points
        signal_points = []
        for sig in ticker_signals:
            point = ChartSignalPoint(
                date=sig.detected_at if hasattr(sig, 'detected_at') else datetime.now(UTC),
                anomaly_sigma=sig.anomaly_sigma if hasattr(sig, 'anomaly_sigma') else 0,
                signal_score=50 + (sig.anomaly_sigma * 20) if hasattr(sig, 'anomaly_sigma') else 50,
                frp_mw=sig.frp_mw if hasattr(sig, 'frp_mw') else 0,
                facility_name=sig.facility_name if hasattr(sig, 'facility_name') else 'Unknown',
                direction='BULLISH' if sig.anomaly_sigma > 0 else 'BEARISH'
            )
            signal_points.append(point)

        # Mark earnings dates on signal points
        for point in signal_points:
            for earn in earnings:
                earn_date = earn.get('date')
                if earn_date and isinstance(earn_date, datetime):
                    if abs((point.date - earn_date).days) < 1:
                        point.is_earnings_date = True
                        point.earnings_eps_estimate = earn.get('eps_estimate')

        # Calculate anomaly axis range
        if signal_points:
            sigmas = [p.anomaly_sigma for p in signal_points]
            anomaly_range = (min(sigmas) - 0.5, max(sigmas) + 0.5)
        else:
            anomaly_range = (-3, 3)

        # Calculate signal-price correlation
        correlation = self._calculate_correlation(price_df, signal_points)

        return SignalOverlayChart(
            ticker=ticker,
            company_name=company_info['name'],
            price_data=price_df,
            signal_points=signal_points,
            anomaly_axis_range=anomaly_range,
            earnings_dates=earnings,
            correlation_summary=correlation
        )

    def _calculate_correlation(self,
                              price_df: pd.DataFrame,
                              signal_points: list[ChartSignalPoint]) -> dict[str, float]:
        """
        Calculate correlation between signals and price movements.
        
        Returns:
            Dict with correlation statistics
        """
        if price_df.empty or len(signal_points) < 2:
            return {'price_signal_corr': 0, 'anomaly_return_corr': 0, 'confidence': 0}

        try:
            # Match signal dates to price dates
            signal_dates = [p.date for p in signal_points]
            sigmas = [p.anomaly_sigma for p in signal_points]

            # Get returns for dates where we have signals
            returns = []
            aligned_sigmas = []

            for i, date in enumerate(signal_dates):
                # Find price on or after signal date
                future_prices = price_df[price_df.index >= date.strftime('%Y-%m-%d')]
                if len(future_prices) >= 2:
                    # 5-day forward return
                    entry = future_prices['close'].iloc[0]
                    if len(future_prices) >= 6:
                        exit_price = future_prices['close'].iloc[5]
                    else:
                        exit_price = future_prices['close'].iloc[-1]

                    ret = (exit_price / entry) - 1
                    returns.append(ret)
                    aligned_sigmas.append(sigmas[i])

            if len(returns) < 2:
                return {'price_signal_corr': 0, 'anomaly_return_corr': 0, 'confidence': 0}

            # Calculate correlation
            from scipy.stats import spearmanr

            corr, p_value = spearmanr(aligned_sigmas, returns)

            return {
                'price_signal_corr': round(corr, 3),
                'anomaly_return_corr': round(corr, 3),
                'confidence': round(1 - p_value, 3) if p_value else 0,
                'n_observations': len(returns)
            }

        except Exception as e:
            logger.warning(f"Correlation calculation failed: {e}")
            return {'price_signal_corr': 0, 'anomaly_return_corr': 0, 'confidence': 0}

    def to_plotly_data(self, chart: SignalOverlayChart) -> dict[str, Any]:
        """
        Convert SignalOverlayChart to Plotly-compatible JSON.
        
        Returns:
            Dict with traces and layout for Plotly
        """
        if chart.price_data.empty:
            return {'error': 'No price data available'}

        df = chart.price_data

        # Price candlestick trace
        price_trace = {
            'x': df.index.strftime('%Y-%m-%d').tolist(),
            'open': df['open'].tolist(),
            'high': df['high'].tolist(),
            'low': df['low'].tolist(),
            'close': df['close'].tolist(),
            'type': 'candlestick',
            'name': f"{chart.ticker} Price",
            'yaxis': 'y1'
        }

        # Volume bar trace
        volume_trace = {
            'x': df.index.strftime('%Y-%m-%d').tolist(),
            'y': df['volume'].tolist(),
            'type': 'bar',
            'name': 'Volume',
            'yaxis': 'y3',
            'marker': {'color': 'rgba(100, 100, 100, 0.3)'}
        }

        # Anomaly signal trace (secondary y-axis)
        if chart.signal_points:
            signal_dates = [p.date.strftime('%Y-%m-%d') for p in chart.signal_points]
            signal_values = [p.anomaly_sigma for p in chart.signal_points]
            signal_colors = ['red' if p.direction == 'BEARISH' else 'green' for p in chart.signal_points]

            signal_trace = {
                'x': signal_dates,
                'y': signal_values,
                'type': 'scatter',
                'mode': 'markers+lines',
                'name': 'Thermal Anomaly (σ)',
                'yaxis': 'y2',
                'marker': {
                    'size': 12,
                    'color': signal_colors,
                    'symbol': 'diamond'
                },
                'line': {'color': 'rgba(255, 165, 0, 0.5)', 'width': 1}
            }
        else:
            signal_trace = None

        # Earnings date markers
        shapes = []
        annotations = []
        for earn in chart.earnings_dates:
            if earn.get('date'):
                date_str = earn['date'].strftime('%Y-%m-%d') if isinstance(earn['date'], datetime) else str(earn['date'])
                shapes.append({
                    'type': 'line',
                    'x0': date_str,
                    'x1': date_str,
                    'y0': 0,
                    'y1': 1,
                    'yref': 'paper',
                    'line': {'color': 'purple', 'width': 2, 'dash': 'dash'}
                })
                annotations.append({
                    'x': date_str,
                    'y': 1.05,
                    'yref': 'paper',
                    'text': 'Earnings',
                    'showarrow': False,
                    'font': {'color': 'purple'}
                })

        # Layout
        layout = {
            'title': f"{chart.company_name} ({chart.ticker}) - Satellite Signal Overlay",
            'xaxis': {'title': 'Date', 'rangeslider': {'visible': False}},
            'yaxis': {
                'title': 'Price ($)',
                'side': 'left',
                'domain': [0.3, 1]
            },
            'yaxis2': {
                'title': 'Thermal Anomaly (σ)',
                'side': 'right',
                'overlaying': 'y',
                'showgrid': False,
                'range': chart.anomaly_axis_range
            },
            'yaxis3': {
                'title': 'Volume',
                'side': 'left',
                'domain': [0, 0.2],
                'showgrid': False
            },
            'shapes': shapes,
            'annotations': annotations,
            'height': 600,
            'hovermode': 'x unified'
        }

        # Build traces list
        traces = [price_trace, volume_trace]
        if signal_trace:
            traces.append(signal_trace)

        return {
            'data': traces,
            'layout': layout,
            'correlation': chart.correlation_summary,
            'signal_count': len(chart.signal_points),
            'earnings_count': len(chart.earnings_dates)
        }


# Singleton instance
_overlay: PriceSignalOverlay | None = None

def get_price_signal_overlay() -> PriceSignalOverlay:
    """Get or create the price signal overlay singleton."""
    global _overlay
    if _overlay is None:
        _overlay = PriceSignalOverlay()
    return _overlay


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    overlay = PriceSignalOverlay()

    # ArcelorMittal

    # In production, we fetch real signals from the Intelligence Engine
    # For testing, we can provide an empty list or fetch from DB
    chart = overlay.create_signal_overlay("MT", [], days=90)

    print(f"\nPrice Chart Overlay for {chart.company_name}:")
    print(f"  Price data points: {len(chart.price_data)}")
    print(f"  Signal points: {len(chart.signal_points)}")
    print(f"  Anomaly range: {chart.anomaly_axis_range}")
    print(f"  Correlation: {chart.correlation_summary}")

    # Generate Plotly data
    plotly_data = overlay.to_plotly_data(chart)
    print(f"\nPlotly traces: {len(plotly_data['data'])}")
