"""API for Volatility Estimators."""
import base64
from io import BytesIO

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

import seaborn as sns
import pandas as pd

from loguru import logger

from api_quotes import get_historical_quotes
from volatility.estimators import VolatilityEstimator, multi_window_estimates

logger.level("DEBUG")
plt.set_loglevel("WARNING")

def to_percentage(value: float, _: str) -> dict:
  """Convert value to percentage."""
  return f"{100 * value:.1f}%"

def vol_plot_trend_box(data: pd.DataFrame) -> str:
  """Generate a plot of the trend of the volatility estimates.

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
    gridspec_kw={"width_ratios": [5, 1]})

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
  currs = data.iloc[-1].to_numpy()
  last_date = data.index[-1].strftime("%Y-%m-%d")

  sns.boxplot(
    data,
    notch=True,
    palette="vlag_r",
    fliersize=7,
    flierprops={"marker": "x"},
    ax=ax2,
  )
  sns.stripplot(data, size=2, color=".3", ax=ax2)
  sns.lineplot(currs, color="red", label=last_date, ax=ax2)

  # Formatting
  ax1.yaxis.set_major_formatter(FuncFormatter(to_percentage))
  ax1.set_ylabel("")
  ax1.set_xlabel("")
  ax1.legend(fontsize="small", loc="upper left")
  ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
  ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
  ax2.set_ylabel("")
  ax2.set_yticks([])
  ax2.legend(fontsize="small", loc="lower right")

  plt.tight_layout()

  buf = BytesIO()
  plt.savefig(buf, format="svg", transparent=True)
  buf.seek(0)
  plot = base64.b64encode(buf.read()).decode("utf-8")

  return {
    "plot": plot,
    "data": None,
  }

def vol_plot_est_boxplots(data: pd.DataFrame) -> dict:
  """Plot all estimators and windows in one plot."""
  # Create a mapping for more readable names
  estimator_names = {
    "close_to_close": "Close-to-Close",
    "parkinson": "Parkinson",
    "garman_klass": "Garman-Klass",
    "rogers_satchell": "Rogers-Satchell",
    "yang_zhang": "Yang-Zhang",
    "mean": "Mean",
  }

  df_long = data.melt(ignore_index=True).reset_index()
  df_long.columns = [
    "Index",
    "Estimator",
    "Window",
    "Value",
  ]

  # Replace the estimator names with more readable versions
  df_long["Estimator"] = df_long["Estimator"].map(estimator_names)

  # Plotting
  _, ax = plt.subplots(figsize=(9,4), dpi=600)
  sns.boxplot(
    x="Window",
    y="Value",
    hue="Estimator",
    data=df_long,
    notch=True,
    palette="deep",
    ax=ax,
  )

  # Line plot for "mean" estimator across all windows
  mean_estimator = data.xs("mean", level="Estimator", axis=1).iloc[-1]
  latest_date = data.index[-1].strftime("%Y-%m-%d")
  sns.lineplot(
    data=mean_estimator.values,
    color="red",
    label=f"Mean on {latest_date}",
    dashes=False,
    ax=ax,
  )

  # Formatting
  ax.yaxis.set_major_formatter(FuncFormatter(to_percentage))
  ax.set_ylabel("")
  ax.legend(fontsize="small", loc="upper right")

  # Add "days" to x-axis labels using the actual window values
  ax.set_xticklabels([f"{int(x)} days" for x in df_long["Window"].unique()])

  plt.tight_layout()

  buf = BytesIO()
  plt.savefig(buf, format="svg", transparent=True)
  buf.seek(0)
  plot = base64.b64encode(buf.read()).decode("utf-8")

  # Create statistics table
  stats_table = df_long.groupby(["Estimator", "Window"])["Value"].agg([
    ("Q1", lambda x: x.quantile(0.25)),
    ("median", "median"),
    ("Q3", lambda x: x.quantile(0.75)),
    ("min", "min"),
    ("max", "max"),
    ("last", "last"),
  ])

  # Calculate IQR and bounds
  stats_table["IQR"] = stats_table["Q3"] - stats_table["Q1"]
  stats_table["lower_fence"] = stats_table["Q1"] - 1.5 * stats_table["IQR"]
  stats_table["upper_fence"] = stats_table["Q3"] + 1.5 * stats_table["IQR"]

  # Calculate z-score equivalent using IQR method
  stats_table["relative_position"] = (stats_table["last"] - stats_table["median"]) /\
    stats_table["IQR"]

  # Reorder columns
  stats_table = stats_table[[
    "Q1",
    "median",
    "Q3",
    "IQR",
    "lower_fence",
    "upper_fence",
    "min",
    "max",
    "last",
    "relative_position",
  ]]

  # Format the values as percentages (except relative_position)
  stats_table = stats_table.round(4) * 100
  stats_table["relative_position"] = stats_table["relative_position"] / 100
  stats_table["relative_position"] = stats_table["relative_position"].round(2)

  return {
    "plot": plot,
    "data": stats_table,
  }

def vol_plot_zscore_vix(
  vols: pd.DataFrame,
  vix: pd.DataFrame,
  window: int,
) -> dict:
  """Plot z-score of mean 30 days window estimator."""
  # Data preparation
  data = vols.xs(("mean", window), level=["Estimator","Window"], axis=1)
  data.columns = ["mean"]
  data = data.join(vix["close"])
  data["zscore"] = (data["mean"] - data["mean"].mean()) / data["mean"].std()
  data["close"] = data["close"] / 100
  data["vrp"] = data["close"] - data["mean"]

  # Figure setup
  _, (ax1, ax2) = plt.subplots(
    2, 1,
    figsize=(9,4),
    dpi=600,
  )

  sns.lineplot(
    data["vrp"],
    color="red",
    label=f"^VIX - RV {window} days",
    ax=ax1,
  )

  sns.lineplot(
    data["zscore"],
    color="blue",
    label=f"Z-score for RV {window} days",
    ax=ax2,
  )

  # Formatting
  ax1.set_xticks([])
  ax1.set_xlabel("")
  ax1.set_ylabel("")
  ax1.yaxis.set_major_formatter(FuncFormatter(to_percentage))
  ax1.legend(fontsize="small", loc="upper left")

  ax2.set_xlabel("")
  ax2.set_ylabel("")
  ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
  ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
  plt.setp(ax2.xaxis.get_majorticklabels(), ha="right")
  ax2.legend(fontsize="small", loc="upper left")

  plt.tight_layout()

  buf = BytesIO()
  plt.savefig(buf, format="svg", transparent=True)
  buf.seek(0)
  plot = base64.b64encode(buf.read()).decode("utf-8")

  # Create export data
  data = data.iloc[-14:]
  export_data = pd.DataFrame({
    "Date": data.index.strftime("%Y-%m-%d"),
    "Volatility Risk Premium": data["vrp"].map("{:.2%}".format),
    "Realized Volatility z-score": data["zscore"].map("{:.2f}".format),
  })

  return {
    "plot": plot,
    "data": export_data.to_dict("records"),
  }

def api_vol(config: dict) -> dict:
  """Return volatility data."""
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
    components=True,
  )

  context = {}
  context["start_date"] = spx.index.min().strftime("%Y-%m-%d")
  context["end_date"] = spx.index.max().strftime("%Y-%m-%d")
  context["estimators"] = estimators

  context["mean_mwa_plot"] = vol_plot_trend_box(vols)["plot"]

  context["estimators_plot"] = vol_plot_est_boxplots(vols)["plot"]
  context["estimators_data"] = vol_plot_est_boxplots(vols)["data"]

  context["zscore_vix_plot"] = vol_plot_zscore_vix(vols, vix, window)["plot"]
  context["zscore_vix_data"] = vol_plot_zscore_vix(vols, vix, window)["data"]

  return context
