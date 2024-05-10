"""
Garman-Klass volatility estimator
"""

import math
import numpy as np

def get_estimator(price_data, window, trading_periods=252, clean=False):
    """
    Main method
    """
    log_hl = (price_data['high'] / price_data['low']).apply(np.log)
    log_co = (price_data['close'] / price_data['open']).apply(np.log)

    rs = 0.5 * log_hl**2 - (2*math.log(2)-1) * log_co**2

    def f(v):
        return (trading_periods * v.mean())**0.5

    result = rs.rolling(window=window, center=False).apply(func=f)

    if clean:
        return result.dropna()
    return result
