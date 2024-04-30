"""
Hodges-Tompkins Estimator
"""

import math
import numpy as np

def get_estimator(price_data, window, trading_periods=252, clean=False):
    """
    Main method
    """
    log_return = (price_data['Close'] / price_data['Close'].shift(1)).apply(np.log)

    vol = log_return.rolling(
        window=window,
        center=False
    ).std() * math.sqrt(trading_periods)

    h = window
    n = (log_return.count() - h) + 1

    adj_factor = 1.0 / (1.0 - (h / n) + ((h**2 - 1) / (3 * n**2)))

    result = vol * adj_factor

    if clean:
        return result.dropna()
    else:
        return result
