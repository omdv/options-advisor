"""
Main flask app
TODO environment variable for pickle file
"""
import os
from datetime import datetime, timezone

from flask import Flask, render_template
from api_itm import api_itm
from api_vol import api_vol

app = Flask(__name__)

def get_config():
    """
    Get the configuration
    """
    config = {
        'mode': os.environ.get('MODE'),
        'bucket_name': os.environ.get('S3_BUCKET_NAME'),
        'pickle_path': os.environ.get('ITM_PICKLE_PATH'),
        'quotes_api': os.environ.get('QUOTES_API_KEY')
    }
    return config

@app.route('/')
def itm_report():
    """
    Index page
    """
    config = get_config()
    itm_data = api_itm(config)
    vol_data = api_vol(config)
    rendered_template = render_template(
        'report.html',
        timestamp=datetime.now(timezone.utc).isoformat(timespec='seconds'),
        itm=itm_data,
        vol=vol_data)
    return rendered_template


@app.route('/api/itm')
def predict():
    """
    Predict ITM probability
    """
    config = get_config()
    return api_itm(config)


@app.route('/api/vol')
def volatility():
    """
    Return volatility data
    """
    config = get_config()
    return api_vol(config)


@app.template_filter()
def quote(value):
    """
    Formatter for quotes
    """
    return f"{value:,.2f}"
