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
