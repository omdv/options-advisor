"""
Rogers-Satchell volatility estimator
"""

import numpy as np

def get_estimator(price_data, window, trading_periods=252, clean=False):
    """
    Main method
    """
    log_ho = (price_data['high'] / price_data['open']).apply(np.log)
    log_lo = (price_data['low'] / price_data['open']).apply(np.log)
    log_co = (price_data['close'] / price_data['open']).apply(np.log)

    rs = log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co)

    def f(v):
        return (trading_periods * v.mean())**0.5

    result = rs.rolling(
        window=window,
        center=False
    ).apply(func=f)

    if clean:
        return result.dropna()
    return result
