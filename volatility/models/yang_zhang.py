"""
Yang-Zhang Volatility Estimator
"""

import math
import numpy as np


def get_estimator(price_data, window, trading_periods=252, clean=False):
    """
    Main method
    """
    log_ho = (price_data['high'] / price_data['open']).apply(np.log)
    log_lo = (price_data['low'] / price_data['open']).apply(np.log)
    log_co = (price_data['close'] / price_data['open']).apply(np.log)

    log_oc = (price_data['open'] / price_data['close'].shift(1)).apply(np.log)
    log_oc_sq = log_oc**2

    log_cc = (price_data['close'] / price_data['close'].shift(1)).apply(np.log)
    log_cc_sq = log_cc**2

    rs = log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co)

    close_vol = log_cc_sq.rolling(
        window=window,
        center=False
    ).sum() * (1.0 / (window - 1.0))
    open_vol = log_oc_sq.rolling(
        window=window,
        center=False
    ).sum() * (1.0 / (window - 1.0))
    window_rs = rs.rolling(
        window=window,
        center=False
    ).sum() * (1.0 / (window - 1.0))

    k = 0.34 / (1.34 + (window + 1) / (window - 1))
    result = (open_vol + k * close_vol + (1 - k) * window_rs).apply(np.sqrt)
    result *= math.sqrt(trading_periods)

    if clean:
        return result.dropna()
    else:
        return result
