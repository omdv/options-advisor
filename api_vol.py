"""
API for Volatility Estimators
TODO estimators to be configurable
"""
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import seaborn as sns

from volatility.estimators import VolatilityEstimator, multi_window_estimates
from api_quotes import get_historical_quotes

plt.set_loglevel('WARNING')

def to_percentage(value, _):
    """
    Convert value to percentage
    """
    return f'{100 * value:.1f}%'


def vol_plot_trend_box(data):
    """
    Moving average plot plus box plot
    select only mean estimator
    """

    # Data preparation
    data = data.xs("mean", level="Estimator", axis=1)
    data.columns = data.columns.get_level_values(0)
    min_window = data.columns.min()
    max_window = data.columns.max()

    # Figure setup
    _, (ax1, ax2) = plt.subplots(
        1, 2,
        figsize=(9, 4),
        dpi=600,
        gridspec_kw={'width_ratios': [5, 1]})

    # sns.lineplot(data, ax=ax1, palette="vlag_r", errorbar="sd", dashes=False)
    sns.lineplot(
        data,
        palette="vlag_r",
        errorbar="sd",
        dashes=False,
        ax=ax1)

    # Fill areas between max and min windows
    ax1.fill_between(
        data.index,
        data.loc[:,min_window],
        data.loc[:,max_window],
        where=(data.loc[:,min_window] > data.loc[:,max_window]),
        color=sns.color_palette("coolwarm")[-1],
        linewidth=0,
        alpha=.2)

    ax1.fill_between(
        data.index,
        data.loc[:,min_window],
        data.loc[:,max_window],
        where=(data.loc[:,min_window] <= data.loc[:,max_window]),
        color=sns.color_palette("coolwarm")[0],
        linewidth=0,
        alpha=.2)

    # Second subplot
    currs = data.iloc[-1].values

    sns.boxplot(
        data,
        notch=True,
        palette="vlag_r",
        fliersize=7,
        flierprops={'marker':'x'},
        ax=ax2)
    sns.stripplot(data, size=2, color=".3", ax=ax2)
    sns.lineplot(currs, color="red", label="current", ax=ax2)

    # Formatting
    ax1.yaxis.set_major_formatter(FuncFormatter(to_percentage))
    ax1.set_ylabel("")
    ax1.set_xlabel("")
    ax1.legend(fontsize='small', loc='upper left')
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax2.set_ylabel("")
    ax2.set_yticks([])
    ax2.legend(fontsize='small', loc='lower right')

    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='svg', transparent=True)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


def vol_plot_est_boxplots(data):
    """
    Plot all estimators and windows in one plot
    """

    df_long = data.stack(level=[0, 1], future_stack=True).reset_index()
    df_long.columns = ['Index', 'Estimator', 'Window', 'Value']

    # Plotting
    _, ax = plt.subplots(figsize=(9,4), dpi=600)
    sns.boxplot(
        x='Window',
        y='Value',
        hue='Estimator',
        data=df_long,
        notch=True,
        palette='deep')

    # Line plot for "mean" estimator across all windows
    mean_estimator = data.xs("mean", level="Estimator", axis=1).iloc[-1]
    sns.lineplot(
        data=mean_estimator.values,
        color="red",
        dashes=False, ax=ax)

    # Formatting
    ax.yaxis.set_major_formatter(FuncFormatter(to_percentage))
    ax.set_ylabel("")
    ax.legend(fontsize='small', loc='upper right')

    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='svg', transparent=True)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


def vol_plot_zscore_vix(vols, vix, window):
    """
    Plot z-score of mean 30 days window estimator
    """

    # Data preparation
    data = vols.xs(("mean", window), level=["Estimator","Window"], axis=1)
    data.columns = ["mean"]
    data = data.join(vix['close'])
    data['zscore'] = (data['mean'] - data['mean'].mean()) / data['mean'].std()
    data['close'] = data['close']/100
    data['vrp'] = data['close'] - data['mean']

    # Figure setup
    _, (ax1, ax2) = plt.subplots(
        2, 1,
        figsize=(9,4),
        dpi=600
    )

    sns.lineplot(
        data['vrp'],
        color="red",
        label=f"VIX - {window}d mean",
        ax=ax1
    )

    sns.lineplot(
        data['zscore'],
        color="blue",
        label=f"{window}d mean z-score",
        ax=ax2
    )

    # Formatting
    ax1.set_xticks([])
    ax1.set_xlabel("")
    ax1.set_ylabel("")
    ax1.yaxis.set_major_formatter(FuncFormatter(to_percentage))
    ax1.legend(fontsize='small', loc='upper left')

    ax2.set_xlabel("")
    ax2.set_ylabel("")
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax2.legend(fontsize='small', loc='upper left')

    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='svg', transparent=True)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


def api_vol(config):
    """
    Main function to return volatility data
    """
    estimators = [
        "close_to_close",
        "parkinson",
        "garman_klass",
        "rogers_satchell",
        "yang_zhang",
    ]

    windows = [10, 22, 66, 100]
    window = 22 # for z-score plot

    spx = get_historical_quotes(config, "^SPX")
    vix = get_historical_quotes(config, "^VIX")

    ens = VolatilityEstimator(estimators=estimators)
    vols = multi_window_estimates(
        estimator=ens,
        price_data=spx,
        windows=windows,
        components=True)

    context = {}
    context['start_date'] = spx.index.min().strftime('%Y-%m-%d')
    context['end_date'] = spx.index.max().strftime('%Y-%m-%d')
    context['estimators'] = estimators

    # First plot for mean estimtor
    context['mean_mwa_plot'] = vol_plot_trend_box(vols)

    # Second plot for all estimators
    context['estimators_boxplot'] = vol_plot_est_boxplots(vols)

    # Third plot for z-score of 30-day mean estimator
    context['zscore_vix'] = vol_plot_zscore_vix(vols, vix, window)

    return context
