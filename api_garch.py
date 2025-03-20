"""GARCH models for volatility forecasting."""

import base64
from io import BytesIO

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import seaborn as sns
import arch

from api_quotes import get_historical_quotes


def to_percentage(value: float, _: str) -> str:
  """Convert value to percentage."""
  return f"{value:.1f}%"

def forecast(
  models: list,
  quotes: pd.DataFrame,
  horizon: int = 22,
) -> pd.DataFrame:
  """Perform GARCH forecast."""
  end_date = quotes.index[-1]
  working_dates = pd.bdate_range(
    end_date + pd.Timedelta(days=1),
    periods=horizon,
  )
  results = pd.DataFrame(index=quotes.index.append(working_dates))

  for model, label in models:
    fitted = model.fit(
      disp="off",
      update_freq=0,
      show_warning=False,
    )

    annualized_volatility = fitted.conditional_volatility * (252 ** 0.5)
    results.loc[quotes.index, label] = annualized_volatility

    # Forecast section
    am_forecast = fitted.forecast(horizon=horizon)
    predicted_volatility = (am_forecast.variance*252) ** 0.5

    results.loc[working_dates, label] = predicted_volatility.to_numpy()[0]

  return results


def forecast_plot(volatilities: pd.DataFrame) -> str:
  """Plot the forecast."""
  # Figure setup
  _, ax1 = plt.subplots(
    figsize=(9, 3),
    dpi=600,
  )

  sns.lineplot(
    volatilities,
    color=sns.color_palette("vlag_r")[-1],
    dashes=False,
    ax=ax1,
  )

  # Formatting
  ax1.yaxis.set_major_formatter(FuncFormatter(to_percentage))
  ax1.set_ylabel("")
  ax1.set_xlabel("")
  ax1.legend(fontsize="small", loc="upper left")
  ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
  ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
  plt.setp(ax1.xaxis.get_majorticklabels(), ha="right")

  # Add horizontal line for today
  today = pd.Timestamp.today().date()
  ax1.axvline(
    today,
    color="black",
    linestyle="-",
    linewidth=0.1,
  )
  ax1.axvspan(
    today,
    volatilities.index[-1],
    facecolor="red",
    alpha=0.1,
  )
  plt.tight_layout()

  buf = BytesIO()
  plt.savefig(buf, format="svg", transparent=True)
  buf.seek(0)
  return base64.b64encode(buf.read()).decode("utf-8")


def get_models(quotes: pd.DataFrame) -> list:
  """Construct GARCH models."""
  returns = 100*quotes["close"].pct_change().dropna()

  return [
    [arch.arch_model(returns, vol="GARCH", p=1, q=1), "GARCH(1,1)"],
  ]

def api_garch(config: dict) -> dict:
  """Orchestrate GARCH forecast."""
  spx = get_historical_quotes(config, "^SPX")

  models = get_models(spx)

  context = {}
  context["start_date"] = spx.index.min().strftime("%Y-%m-%d")
  context["end_date"] = spx.index.max().strftime("%Y-%m-%d")

  garch_forecast = forecast(models, spx)
  garch_plot = forecast_plot(garch_forecast)

  context["garch_plot"] = garch_plot
  return context
