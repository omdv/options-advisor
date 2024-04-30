"""
API for Volatility View
TODO estimators to be configurable
"""
import base64
from io import BytesIO
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import seaborn as sns
import yfinance as yf
from backend.volatility.estimators import VolatilityEstimator, multi_window_estimates


def volatility_plot_mwa(data):
    """
    Moving average plot plus box plot
    """

    def to_percentage(value, _):
        return f'{100 * value:.1f}%'

    # clean up column names
    data.columns = data.columns.str.replace(
        r'mean_(\d+)d',
        r'\1 days',
        regex=True)

    # Figure setup
    plt.figure(figsize=(9,5), dpi=600)
    left, width = 0.09, 0.65
    bottom, height = 0.1, 0.85
    left_h = left+width+0.02
    rect_left = [left, bottom, width, height]
    rect_right = [left_h, bottom, 0.17, height]
    left = plt.axes(rect_left)
    right = plt.axes(rect_right)

    # First subplot using Seaborn
    sns.lineplot(
        data,
        palette="vlag_r",
        errorbar="sd",
        dashes=False,
        ax=left)

    # Setting date-specific x-ticks every 20 days
    end_date = pd.Timestamp('today')
    start_date = end_date - pd.Timedelta(days=60)
    left.set_xlim(start_date, end_date)

    # Set x-axis major ticks to every 15 days
    left.xaxis.set_major_locator(mdates.DayLocator(interval=15))
    left.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    left.legend(fontsize='small')

    # Rotate date labels to prevent overlap
    plt.gcf().autofmt_xdate()

    # Second subplot
    sns.boxplot(data, notch=True, palette="vlag_r", ax=right)
    sns.stripplot(data, size=2, color=".3", ax=right)
    sns.lineplot(data.mean(axis=0), color="blue", zorder=5, label="mean", ax=right)
    sns.lineplot(data.iloc[-1], color="red", ax=right, label="current")

    # change x-ticks
    current_labels = [item.get_text() for item in right.get_xticklabels()]
    right.set_xticks(range(len(current_labels)))
    right.set_xticklabels(range(1, len(current_labels) + 1))
    right.legend(fontsize='small')

    # change y-ticks
    left.yaxis.set_major_formatter(FuncFormatter(to_percentage))
    right.yaxis.set_major_formatter(FuncFormatter(to_percentage))
    right.yaxis.tick_right()
    right.set_ylabel("")

    buf = BytesIO()
    plt.savefig(buf, format='svg', transparent=True)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


def api_vol():
    """
    Main function to return volatility data
    """
    estimators = [
        "close_to_close",
        "parkinson",
        "garman_klass",
        "hodges_tompkins",
        "rogers_satchell",
        "yang_zhang",
    ]

    windows = [30, 60, 90, 120]

    spx = yf.Ticker("^SPX")
    quotes = spx.history(period="1y")
    ens = VolatilityEstimator(estimators=estimators)
    vols = multi_window_estimates(
        estimator=ens,
        price_data=quotes,
        windows=windows,
        components=False)

    context = {}
    context['start_date'] = quotes.index.min().strftime('%Y-%m-%d')
    context['end_date'] = quotes.index.max().strftime('%Y-%m-%d')
    context['estimators'] = estimators
    context['mwa_plot'] = volatility_plot_mwa(vols)

    return context
