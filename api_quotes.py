"""Routines to get market quotes."""

import pandas as pd
import requests
from loguru import logger

logger.level("DEBUG")

def get_historical_quotes(
  config: dict,
  ticker: str,
  start_date: str | None = None,
  end_date: str | None = None,
  n_days: int = 356,
) -> pd.DataFrame:
  """Get quotes for a given ticker."""
  api_key = config["quotes_api_key"]

  if start_date is None and end_date is None:
    end_date = pd.Timestamp.now().strftime("%Y-%m-%d")
    start_date = (pd.Timestamp.now() - pd.Timedelta(days=n_days)).strftime("%Y-%m-%d")

  logger.debug(f"Getting quotes for {ticker} from {start_date} to {end_date}")
  url = "https://financialmodelingprep.com/api/v3/historical-price-full/"
  url = url + f"{ticker}?from={start_date}&to={end_date}&apikey={api_key}"

  try:
    response = requests.get(url, timeout=5)
    response.raise_for_status()
  except requests.exceptions.RequestException as e:
    logger.error(f"Failed to fetch data from quotes api: {e}")
    return None

  try:
    data = pd.DataFrame(response.json()["historical"])
  except ValueError:
    logger.error(f"Failed to parse data from quotes api: {response.json()}")
    return None

  data["date"] = pd.to_datetime(data["date"])
  data = data.set_index("date")
  del data["label"]  # Remove only non-numeric column
  data = data.apply(pd.to_numeric)
  return data.sort_index(ascending=True)


def _get_last_quote(config: dict, ticker: str) -> dict:
  """Get the latest quote for a given ticker."""
  api_key = config["quotes_api_key"]
  url = "https://financialmodelingprep.com/api/v3/quote/"
  url = url + f"{ticker}?apikey={api_key}"

  try:
    response = requests.get(url, timeout=5)
    response.raise_for_status()
  except requests.exceptions.RequestException as e:
    logger.error(f"Failed to fetch data from quotes api: {e}")
    return None

  data = response.json()[0]
  quote = {}
  try:
    quote["open"] = float(data["open"])
    quote["previous_close"] = float(data["previousClose"])
    quote["datetime"] = pd.to_datetime(data["timestamp"], unit="s")
  except ValueError:
    logger.error(f"Failed to parse quote for {ticker}")
    return None

  return quote


def get_vix_open(config: dict) -> tuple[float, pd.Timestamp]:
  """Get the Open VIX price quotes API."""
  quote = _get_last_quote(config, "^VIX")
  vix_open = quote["open"]
  return vix_open, quote["datetime"]

def get_otc_open(config: dict) -> tuple[float, pd.Timestamp]:
  """Get the Open to Prev.Close change for SPX."""
  quote = _get_last_quote(config, "^SPX")
  otc = (quote["open"] - quote["previous_close"]) / quote["previous_close"] * 100
  return otc, quote["datetime"]


def get_economic_events(config: dict) -> pd.DataFrame:
  """Get economic events for current and next week."""
  api_key = config["quotes_api_key"]
  base_url = "https://financialmodelingprep.com/api/v3/economic_calendar"

  # Calculate date ranges
  today = pd.Timestamp.now()
  start_date = today - pd.Timedelta(days=today.dayofweek)  # Start of current week
  end_date = start_date + pd.Timedelta(days=13)  # End of next week

  params = {
      "from": start_date.strftime("%Y-%m-%d"),
      "to": end_date.strftime("%Y-%m-%d"),
      "apikey": api_key,
  }

  try:
      response = requests.get(base_url, params=params, timeout=5)
      response.raise_for_status()
  except requests.exceptions.RequestException as e:
      logger.error(f"Failed to fetch economic events: {e}")
      return None

  try:
      events = response.json()
      formatted_events = []
      for event in events:
        formatted_event = {
          "date": event["date"],
          "country": event["country"],
          "event": event["event"],
          "impact": event["impact"],
          "actual": event["actual"],
          "previous": event["previous"],
          "estimate": event["estimate"],
          "unit": event["unit"],
        }
        formatted_events.append(formatted_event)

      df_events = pd.DataFrame(formatted_events)
      df_events["date"] = pd.to_datetime(df_events["date"], utc=True)

      # Only include US events
      df_events = df_events[df_events["country"] == "US"]
      df_events = df_events[(df_events["impact"] == "High")]
      df_events = df_events.set_index("date")

      del df_events["country"]
      del df_events["unit"]

      logger.debug(f"Economic events: {df_events}")
      return df_events.sort_values("date")

  except (ValueError, KeyError) as e:
      logger.error(f"Failed to parse economic events: {e}")
      return None
