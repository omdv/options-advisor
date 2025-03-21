"""Standalone renderer of jinja2 template."""

import os
import requests

from loguru import logger
from datetime import datetime, UTC
from jinja2 import Environment

from api_vol import api_vol
from api_garch import api_garch
from api_assistant import api_assistant
from io_utils import save_to_s3, read_from_s3

logger.level("DEBUG")

def send_notification(ntfy_topic: str, data: dict) -> None:
  """Send message via ntfy.sh."""
  ntfy_url = f"https://ntfy.sh/{ntfy_topic}"
  summary = data["summary"]
  forecast = data["forecast"]
  events = "\n".join([
    f"{datetime.strptime(time, '%Y-%m-%dT%H:%M:%S%z').strftime('%Y-%m-%d')}: {event}"
    for time, event in data["events"]
  ])

  # Generate the message
  message = f"📝 Summary\n{summary}\n\n📊 Forecast\n{forecast}\n\n📅 Events\n{events}"

  try:
    requests.post(
      ntfy_url,
      data=message.encode("utf-8"),
      headers={
        "Title": "Volatility Report for " + datetime.now(UTC).strftime("%Y-%m-%d"),
        "Priority": "default",
        "Tags": "volatility-report",
      },
      timeout=10,
    )
  except requests.exceptions.RequestException as e:
    logger.error(f"Failed to send notification: {e}")

def get_config() -> dict:
  """Get the configuration."""
  config = {
    "mode": os.environ.get("MODE"),
    "bucket_name": os.environ.get("S3_BUCKET_NAME"),
    "pickle_path": os.environ.get("ITM_PICKLE_PATH"),
    "quotes_api_key": os.environ.get("QUOTES_API_KEY"),
    "openai_api_key": os.environ.get("OPENAI_API_KEY"),
    "ntfy_topic": os.environ.get("NTFY_TOPIC"),
  }
  logger.info(f"Config: {config}")
  return config

def handler(_: dict, context: dict) -> str:
  """Lambda handler."""
  logger.info("Starting...")
  cfg = get_config()

  def quote(value: float) -> str:
    """Formatter for quotes."""
    return f"{value:,.2f}"

  # Create a new Jinja2 environment
  env = Environment(autoescape=True)

  # Register the 'quote' filter
  env.filters["quote"] = quote

  # Read the template from S3
  template_source = read_from_s3(cfg, "templates/report.html", decode=True)

  # Create the template
  template = env.from_string(template_source)
  logger.info("Template read from S3")

  # Get the volatility data
  vol_data = api_vol(cfg)
  logger.debug(f"API VOL: {vol_data.keys()}")

  # Get the GARCH data
  garch_data = api_garch(cfg)
  logger.debug(f"API GARCH: {garch_data.keys()}")

  # Get the assistant data
  assistant_data = api_assistant(
    cfg,
    vol_data["estimators_data"],
    vol_data["zscore_vix_data"],
  )
  logger.debug(f"API ASSISTANT: {assistant_data}")

  send_notification(cfg["ntfy_topic"], assistant_data)

  # Generate the context for the template
  context = {
    "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
    "vol": vol_data,
    "garch": garch_data,
    "assistant": assistant_data,
  }

  # Render the template
  rendered_template = template.render(context)

  # Save the rendered template to S3
  save_to_s3(
    cfg,
    "index.html",
    rendered_template,
    content_type="text/html",
  )

  logger.info("Rendered template saved to S3")
  return "Done"

if __name__ == "__main__":
  handler(None, None)
