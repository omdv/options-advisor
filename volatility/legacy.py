"""
Calculate volatility tearsheet
"""
import base64
import datetime
from io import BytesIO
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
from tabulate import tabulate
from sparklines import sparklines
from volatility import models, volest


ESTIMATORS = [
    "close_to_close",
    "parkinson",
    "garman_klass",
    "hodges_tompkins",
    "rogers_satchell",
    "yang_zhang",
    "mean"
]

def volatility_table(price_data, windows, sparkline_size):
    """
    Return volatility table for a given set of windows
    """

    table_data = []
    for window in windows:
        results = []
        for e in ESTIMATORS[:-1]:
            result = globals()[e](price_data, window=window)
            results.append(result)
            history = result[-sparkline_size:]
            sparkline_string = sparklines(history)[0]
            table_data.append([
                e,
                window,
                result.iloc[-1],
                history,
                sparkline_string])

        # Add the mean method
        mean_result = pd.concat(results, axis=1).mean(axis=1)
        mean_history = mean_result[-sparkline_size:]
        mean_sparkline_string = sparklines(mean_history)[0]
        table_data.append([
            "mean",
            window,
            mean_result.iloc[-1],
            mean_history,
            mean_sparkline_string])

    # create dataframe and sort before return
    table = pd.DataFrame(
        table_data,
        columns=["estimator", "window", "current", "history", "sparkline"])
    table["estimator"] = pd.Categorical(
        table["estimator"],
        categories=ESTIMATORS,
        ordered=True)
    table = table.sort_values(["estimator", "window"])
    return table


def console_table(price_data, windows, sparkline_size):
    """
    Styling for console table
    """
    table = volatility_table(price_data, windows, sparkline_size)
    table["result"] = table["current"].map("{:0.4f}".format) + " " + table["sparkline"]
    table = table.drop(columns=["current", "sparkline", "history"])
    table = table.pivot(index="method", columns="window", values="result")

    # sorting
    table.columns = table.columns.astype(int)
    table = table.sort_index(axis=1)
    table.columns = table.columns.astype(str) + " days"

    print(tabulate(table, headers="keys"))


def sparkline_img(data, figsize=(0.5, 0.1), **kwags):
    """
    Returns a HTML image tag containing a base64 encoded sparkline style plot
    """
    data = list(data)

    _, ax = plt.subplots(1, 1, figsize=figsize, **kwags)
    ax.plot(data, linewidth=0.6)
    for _,v in ax.spines.items():
        v.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])

    plt.plot(len(data) - 1, data[len(data) - 1], 'r.', markersize=1.0)
    ax.fill_between(range(len(data)), data, len(data)*[min(data)], alpha=0.5)

    img = BytesIO()
    plt.savefig(img)
    img.seek(0)
    plt.close()
    return f'<img src="data:image/png;base64,{base64.b64encode(img.read()).decode()}">'


def html_table(price_data, windows, sparkline_size):
    """
    Styling for HTML table
    """
    table = volatility_table(price_data, windows, sparkline_size)

    # styling
    table["combined"] = table["current"].map("{:0.4f}".format) + " " + table["history"].apply(sparkline_img)
    table = table.drop(columns=["current", "sparkline", "history"])
    table = table.pivot(index="method", columns="window", values="combined")

    # sorting
    table.columns = table.columns.astype(int)
    table = table.sort_index(axis=1)
    table.columns = table.columns.astype(str) + " days"

    # clean up names
    table.columns.name = None
    table.index.name = None
    table.to_html("./tmp/volatility_table.html", escape=False)


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

   # initialize class
    vol = volest.VolatilityEstimator(
    price_data=historical_data,
    estimator=estimator,
    bench_data=spx_price_data
)