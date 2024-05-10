"""
Exponentially Weighted Moving Average (EWMA) model.
"""

import numpy as np

def get_estimator(price_data, window, lambda_=0.94, trading_periods=252, clean=False):
    """
    Compute the exponentially weighted moving average (EWMA) volatility of a series of returns.
    
    Parameters:
    - price_data (pd.Series): Time series of price_data
    - lambda_ (float): Smoothing parameter (decay factor)

    Returns:
    - pd.Series: EWMA volatility estimates
    """
    log_return = (price_data['close'] / price_data['close'].shift(1)).apply(np.log)

    def compute_ewma(series, lambda_):
        """ Helper function to compute EWMA on a series of returns. """
        ewma_var = np.zeros_like(series)
        ewma_var[0] = series.var()  # Initialize with the variance of the initial returns

        for t in range(1, len(series)):
            ewma_var[t] = lambda_ * ewma_var[t - 1] + (1 - lambda_) * series.iloc[t]**2

        ewma_vol = np.sqrt(trading_periods * ewma_var)
        return ewma_vol

    # Use a rolling window to compute EWMA volatility
    ewma_vol = log_return.rolling(window=window).apply(
        lambda x: compute_ewma(x, lambda_)[-1], raw=False)

    if clean:
        return ewma_vol.dropna()
    return ewma_vol
