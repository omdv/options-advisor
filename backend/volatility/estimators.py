"""
Volatility estimator class
TODO add tests
"""
import pandas as pd
import yfinance as yf
from backend.volatility import models


class VolatilityEstimator(object):
    """
    Estimator averaging multiple estimators
    """

    def __init__(self, estimators):
        self._estimators = estimators

    def _get_estimator(
            self,
            window,
            price_data,
            components):
        """
        Selector for volatility estimator
        
        Parameters
        ----------
        window : int
            Rolling window for which to calculate the estimator
        
        Returns
        -------
        y : pandas.DataFrame
            Estimator series values
        """
        result = pd.concat(
            [getattr(models, estimator).get_estimator(
            price_data=price_data,
            window=window,
            clean=False
            ) for estimator in self._estimators],
            axis=1
        )
        result['mean'] = result.dropna(axis=0).mean(axis=1, skipna=False)
        result.columns = pd.MultiIndex.from_product(
            [self._estimators + ['mean'], [window]],
            names=['Estimator', 'Window'])

        if not components:
            result = result.loc[:, ['mean']]

        result.index = price_data.index.strftime("%Y-%m-%d")
        return result

    def estimate(self, price_data, window, components=False, clean=True):
        """
        Estimate volatility
        """
        results = self._get_estimator(
            window=window,
            price_data=price_data,
            components=components
        )
        if clean:
            results = results.dropna()
        return results


def multi_window_estimates(
        estimator,
        price_data,
        windows,
        components=False):
    """
    Calculate a volatility estimator for multiple windows
    
    Parameters
    ----------
    estimator : str
        Name of the estimator to use
    price_data : pandas.DataFrame
        Price data
    windows : tuple
        Tuple of window sizes for which to calculate the estimator
    
    Returns
    -------
    y : pandas.DataFrame
        DataFrame containing the estimator values for each window size
    """

    result = pd.concat(
        [estimator.estimate(
            price_data=price_data,
            window=window,
            components=components) for window in windows],
        axis=1
    )
    return result


ESTIMATORS = [
    "close_to_close",
    "parkinson",
    "garman_klass",
    "hodges_tompkins",
    "rogers_satchell",
    "yang_zhang",
]


if __name__ == "__main__":
    spx = yf.Ticker("^SPX")
    quotes = spx.history(
        start="2023-01-01",
        end="2023-06-01")
    ens = VolatilityEstimator(estimators=ESTIMATORS)

    vols = ens.estimate(quotes, window=20, components=True, clean=False)
    # print(vols)

    vols = ens.estimate(quotes, window=20, components=False, clean=False)
    # print(vols)

    # print(vols.iloc[-1]["mean_20d"])

    ests = multi_window_estimates(
            ens,
            quotes,
            windows=(60, 90),
            components=True)
    print(ests.head())
