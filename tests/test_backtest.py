import pytest
import pandas as pd
import numpy as np
from src.backtest.engine import BacktestEngine, CostModel, BacktestResult

def test_sharpe_without_ci_raises_value_error():
    # Attempting to validate a result with missing CI
    with pytest.raises(ValueError, match="confidence interval"):
        result = BacktestResult(
            sharpe=1.2,
            sharpe_ci_lower_95=None, # Missing
            sharpe_ci_upper_95=1.5,
            max_drawdown=0.1,
            annualised_return=0.15,
            hit_rate=0.55,
            turnover_annual=0.5,
            n_observations=100
        )
        result.validate()

def test_zero_cost_backtest_is_rejected():
    with pytest.raises(ValueError, match="costs"):
        CostModel(bid_ask_bps_by_mcap_tier={"large_cap": 0.0}, commission_bps=0.0)

def test_backtest_engine_produces_ci():
    costs = CostModel(bid_ask_bps_by_mcap_tier={"large_cap": 2.0})
    engine = BacktestEngine(costs)
    
    # Generate 2 years of daily returns
    returns = pd.Series(np.random.normal(0.0005, 0.01, 504))
    result = engine.run_backtest(returns)
    
    assert result.sharpe_ci_lower_95 is not None
    assert result.sharpe_ci_upper_95 is not None
    assert result.sharpe_ci_lower_95 < result.sharpe < result.sharpe_ci_upper_95
