"""
Calculate volatility tearsheet for console
"""
import base64
import datetime
from io import BytesIO
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
from tabulate import tabulate
from sparklines import sparklines
from volatility.estimators import VolatilityEstimator, EnsembleEstimator


ESTIMATORS = [
    "close_to_close",
    "parkinson",
    "garman_klass",
    "hodges_tompkins",
    "rogers_satchell",
    "yang_zhang",
]


def volatility_table(
        estimators,
        price_data,
        windows,
        sparkline_size):
    """
    Generate a volatility table.

    This function calculates the volatility for different estimators and window sizes
    based on the given price data. It returns a table containing the results.

    Parameters:
    - estimators (list): A list of estimator names.
    - price_data (pd.DataFrame): A DataFrame containing the price data.
    - windows (list): A list of window sizes.
    - sparkline_size (int): The size of the sparkline to be displayed.

    Returns:
    - table (pd.DataFrame): A DataFrame containing the volatility results.

    """
    models = [VolatilityEstimator(e) for e in estimators]

    # table_data = []
    # for window in windows:
    #     results = []
    #     for e in estimators:
    #         result = globals()[e](price_data, window=window)
    #         results.append(result)
    #         history = result[-sparkline_size:]
    #         sparkline_string = sparklines(history)[0]
    #         table_data.append([
    #             e,
    #             window,
    #             result.iloc[-1],
    #             history,
    #             sparkline_string])

    #     # Add the mean method
    #     mean_result = pd.concat(results, axis=1).mean(axis=1)
    #     mean_history = mean_result[-sparkline_size:]
    #     mean_sparkline_string = sparklines(mean_history)[0]
    #     table_data.append([
    #         "mean",
    #         window,
    #         mean_result.iloc[-1],
    #         mean_history,
    #         mean_sparkline_string])

    # # create dataframe and sort before return
    # table = pd.DataFrame(
    #     table_data,
    #     columns=["estimator", "window", "current", "history", "sparkline"])
    # table["estimator"] = pd.Categorical(
    #     table["estimator"],
    #     categories=ESTIMATORS,
    #     ordered=True)
    # table = table.sort_values(["estimator", "window"])
    # return table


# def console_tearsheet(price_data, windows, sparkline_size):
#     """
#     Styling for console table
#     """
#     table = volatility_table(price_data, windows, sparkline_size)
#     table["result"] = table["current"].map("{:0.4f}".format) + " " + table["sparkline"]
#     table = table.drop(columns=["current", "sparkline", "history"])
#     table = table.pivot(index="method", columns="window", values="result")

#     # sorting
#     table.columns = table.columns.astype(int)
#     table = table.sort_index(axis=1)
#     table.columns = table.columns.astype(str) + " days"

#     print(tabulate(table, headers="keys"))


if __name__ == "__main__":
    # spx = yf.Ticker("^SPX")
    # historical_data = spx.history(
    #     start="2023-01-01",
    #     end=datetime.datetime.now().strftime("%Y-%m-%d"))
    # historical_data.to_csv("./tmp/price_data.csv")
    historical_data = pd.read_csv("./tmp/price_data.csv")
    # console_table(historical_data, [7, 15, 30, 60], 14)
    # html_table(historical_data, [7, 15, 30, 60], 30)
    # print(models.close_to_close.get_estimator(historical_data, window=30))
    volatility_table(["close_to_close", "parkinson"], historical_data, [7, 15, 30, 60], 14)