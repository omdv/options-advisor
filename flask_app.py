"""
Main flask app
"""
from flask import Flask, render_template
from volatility.lookup import api_call

app = Flask(__name__)

@app.route('/')
def itm_report():
    """
    Index page
    """
    itm_data = api_call()
    return render_template('report.html', ctx=itm_data)

@app.route('/api/itm')
def predict():
    """
    Predict ITM probability
    """
    return api_call()

@app.template_filter()
def quote(value):
    """
    Formatter for quotes
    """
    return "{:,.2f}".format(value)
