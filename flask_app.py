"""
Main flask app
TODO environment variable for pickle file
"""
from flask import Flask, render_template
from backend.itm_api import api_itm
from backend.vol_api import api_vol

app = Flask(__name__)


@app.route('/')
def itm_report():
    """
    Index page
    """
    itm_data = api_itm()
    vol_data = api_vol()
    return render_template('report.html', itm=itm_data, vol=vol_data)


@app.route('/api/itm')
def predict():
    """
    Predict ITM probability
    """
    return api_itm()


@app.route('/api/vol')
def volatility():
    """
    Return volatility data
    """
    return api_vol()


@app.template_filter()
def quote(value):
    """
    Formatter for quotes
    """
    return f"{value:,.2f}"
