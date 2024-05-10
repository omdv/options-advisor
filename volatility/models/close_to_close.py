"""
Implementing close-to-close vol estimator
"""

import math
import numpy as np

def get_estimator(price_data, window, trading_periods=252, clean=False):
    """
    Main method
    """
    log_return = (price_data['close'] / price_data['close'].shift(1)).apply(np.log)

    result = log_return.rolling(
        window=window,
        center=False
    ).std() * math.sqrt(trading_periods)

    if clean:
        return result.dropna()
    return result
