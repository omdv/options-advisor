"""
Create volatility tearsheet in html
"""
import yfinance as yf
import datetime as dt
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from volatility.estimators import VolatilityEstimator, multi_window_estimates



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
        windows):
    """
    Generate a volatility table.

    This function calculates the volatility for different estimators and window sizes
    based on the given price data. It returns a table containing the results.

    Parameters:
    - estimators (list): A list of estimator names.
    - price_data (pd.DataFrame): A DataFrame containing the price data.
    - windows (list): A list of window sizes.

    Returns:
    - table (pd.DataFrame): A DataFrame containing the volatility results.

    """
    est = VolatilityEstimator(estimators)
    result = multi_window_estimates(
        est,
        price_data,
        windows,
        components=False)

    return result


def load_price_data():
    """
    Load price data.
    """
    # data = yf.download("^SPX", start="2020-01-01", end="2021-01-01")
    # data.to_csv("./tmp/price_data.csv")
    data = pd.read_csv("./tmp/price_data.csv")
    return data


def html_report():
    """
    Create a volatility report in HTML format.

    This function generates a volatility report in HTML format. It returns a string
    containing the HTML code.

    Returns:
    - html (str): A string containing the HTML code of the report.

    """

    data = load_price_data()
    volatilities = volatility_table(
        ESTIMATORS,
        data,
        [7, 15, 30, 60]
    )

    environment = Environment(loader=FileSystemLoader("./templates/"))
    template = environment.get_template("report.html")

    report_filename = "report_out.html"
    context = {
        "report_timestamp": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "report_date": dt.datetime.now().strftime("%Y-%m-%d"),
        "volatility_table": volatilities.to_html()
    }

    with open(report_filename, mode="w", encoding="utf-8") as results:
        results.write(template.render(context))


if __name__ == "__main__":
    html_report()
