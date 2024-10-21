"""
Main flask app
TODO environment variable for pickle file
"""
from flask import Flask
from lambda_function import get_config, handler
from api_itm import api_itm
from api_vol import api_vol
from api_garch import api_garch
from api_assistant import api_assistant

app = Flask(__name__)

@app.route('/')
def itm_report():
    """
    Generate index.html file and return it
    """
    handler({}, None)

    # Read the generated index.html file
    with open('index.html', 'r') as file:
        html_content = file.read()

    return html_content


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


@app.route('/api/garch')
def garch():
    """
    Return GARCH data
    """
    config = get_config()
    return api_garch(config)


@app.route('/api/assistant')
def assistant():
    """
    Return assistant data
    """
    config = get_config()
    return api_assistant(config)


@app.template_filter()
def quote(value):
    """
    Formatter for quotes
    """
    return f"{value:,.2f}"
