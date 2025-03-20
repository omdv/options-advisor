"""Main flask app."""

from pathlib import Path
from flask import Flask

from api_assistant import api_assistant
from api_garch import api_garch
from api_itm import api_itm
from api_vol import api_vol
from lambda_function import get_config, handler

app = Flask(__name__)

@app.route("/")
def itm_report() -> str:
  """Generate index.html file and return it."""
  handler({}, None)

  # Read the generated index.html file
  with Path("index.html").open() as file:
    return file.read()


@app.route("/api/itm")
def predict_itm() -> str:
  """Predict ITM probability."""
  config = get_config()
  return api_itm(config)


@app.route("/api/vol")
def volatility() -> str:
  """Return volatility data."""
  config = get_config()
  return api_vol(config)


@app.route("/api/garch")
def garch() -> str:
  """Return GARCH data."""
  config = get_config()
  return api_garch(config)


@app.route("/api/assistant")
def assistant() -> str:
  """Return assistant data."""
  config = get_config()
  return api_assistant(config)


@app.template_filter("quote")
def quote(value: float) -> str:
  """Formatter for quotes."""
  return f"{value:,.2f}"
