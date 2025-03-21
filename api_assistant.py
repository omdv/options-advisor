"""API for Volatility Estimators."""
from loguru import logger
from datetime import datetime, UTC
import openai
import pandas as pd
import json

from api_quotes import get_economic_events

logger.level("INFO")

def api_assistant(
    config: dict,
    estimators_data: pd.DataFrame,
    zscore_vix_data: pd.DataFrame,
) -> dict:
    """Call the OpenAI API."""
    openai.api_key = config["openai_api_key"]

    system_prompt = """
    You are a financial analyst.
    Your response should be simple to understand for a non-financial audience.
    """

    user_prompt = f"""
    Analyze the following statistics for realized volatility estimators
    across several windows and provide insights:
    {estimators_data.to_dict()}

    You have the following economic events for the current and next week.
    Factor this into your analysis and provide forecast for the trend for next week.
    Include specific events and dates that are likely to impact the market.
    Today's date is {datetime.now(UTC).strftime("%Y-%m-%d")}.
    {get_economic_events(config)}

    This is the data for the past 14 days for the difference between the
    ^VIX indicator and the mean realized volatility, denoted as Volatility Risk Premium.
    There is also a Z-score for realized volatility, denoted as Z-score.
    {zscore_vix_data}

    Provide implications of the volatility trend for the strategy
    which is leveraging the volatility risk premium.

    ### JSON output format
    {{
      "summary": "Description of the overall trend. <= 5 sentences",
      "forecast": "Volatility forecast and strategy implications. <= 5 sentences",
      "events": "2-3 events that are likely to impact the market as json array",
        ["event date (iso tz-aware timestamp)", "event name"],
      ],
      "confidence": "High/Medium/Low"
    }}
    """

    logger.debug(f"API ASSISTANT user prompt: {user_prompt}")
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
        max_tokens=5000,
    )
    content = response.choices[0].message.content
    logger.debug(f"API ASSISTANT response: {content}")

    # Parse the response content as JSON
    try:
      parsed_content = json.loads(content)
      if not all(key in parsed_content for key in [
        "summary",
        "forecast",
        "events",
        "confidence",
      ]):
        logger.error("Response missing required keys")
        raise ValueError
    except json.JSONDecodeError:
        logger.error("Failed to parse API response as JSON")
        raise

    return parsed_content
