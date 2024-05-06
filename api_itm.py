"""
Predicting probability of ITM for a given option
this file supposed to be used as a standalone API
"""
import os
import base64
from io import BytesIO

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns

def load_itm_dataframe():
    """
    Load the lookup table from the given path
    """
    path = os.environ.get('ITM_PICKLE_PATH')
    if path is None:
        path = 'itm.pickle'
    return pd.read_pickle(path)


def probs_heatmap(df):
    """
    Generate a heatmap from the given frame
    save as IO buffer and pass as base64 string
    """

    # original_shape = df.values.shape
    # labels = np.array([f"{v:.4f}" if v > 0.01 else '' for v in df.values.flatten()])
    # labels = labels.reshape(original_shape)
    df.replace(0, np.NaN, inplace=True)

    plt.figure(figsize=(9,4), dpi=600)
    sns.heatmap(
        df,
        annot=True,
        fmt='.4f',
        annot_kws={'size': 'small', 'alpha': 0.7},
        linewidths=0.05,
        linecolor="#4c566a",
        cbar_kws={'shrink': 0.8},
        cbar=False,
        cmap='vlag')
    plt.tick_params(axis='both')
    # plt.xticks()
    # plt.yticks()
    plt.xlabel("delta bin", fontweight='bold')
    plt.ylabel("expiration", fontweight='bold')

    buf = BytesIO()
    plt.savefig(buf, format='svg', transparent=True)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


def itm_stats(vix_open, otc_open):
    """
    API-ready function
    """
    df = load_itm_dataframe()
    df['vix_bins'], vix_bins = pd.qcut(df['vix_open'], q=4, retbins=True)
    df['otc_bins'], otc_bins = pd.qcut(df['open_to_close_pct'], q=4, retbins=True)

    # for sample size
    group_sizes = df.groupby(['vix_bins','otc_bins']).size()

    # get probabilities
    probs = pd.pivot_table(
        df,
        values='itm',
        index=['vix_bins', 'otc_bins', 'expiration_weekday'],
        columns=['delta_bin'],
        aggfunc=np.mean)

    vix_bin = pd.cut([vix_open], bins=vix_bins, include_lowest=True)
    otc_bin = pd.cut([otc_open], bins=otc_bins, include_lowest=True)

    response = {}

    result = probs.loc[(vix_bin, otc_bin, slice(None))].reset_index(level=[0,1], drop=True)
    response['probs'] = result.to_html(
        float_format="{:,.4f}".format,
        index_names=False,
        classes='dataframe',
        col_space=10,
    )
    response['probs_heatmap'] = probs_heatmap(result)
    response['total_samples'] = f"{df.shape[0]}"
    response['group_samples'] = f"{group_sizes.loc[(vix_bin, otc_bin)].values[0]}"
    response['min_date'] = df['quote_datetime'].min().strftime('%Y-%m-%d')
    response['max_date'] = df['quote_datetime'].max().strftime('%Y-%m-%d')
    return response


def get_vix_open():
    """
    Get the latest VIX open price
    """
    vix = yf.Ticker('^VIX')
    hist = vix.history(period="1d")
    return hist['Open'].iloc[-1], hist.index[-1]


def get_otc_open():
    """
    Get the latest open to close price
    """
    spx = yf.Ticker('^SPX')
    hist = spx.history(period="7d")
    otc = (hist['Open']-hist['Close'].shift(1)) / hist['Close'].shift(1) * 100
    return otc.iloc[-1], otc.index[-1]


def api_itm():
    """
    API call return
    """
    result = {}
    vix_open, vix_quote_date = get_vix_open()
    otc_open, otc_quote_date = get_otc_open()
    stats = itm_stats(vix_open, otc_open)

    result['gen_timestamp'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
    result['vix_open'] = vix_open
    result['vix_quote_date'] = vix_quote_date.strftime('%Y-%m-%d')
    result['otc_open'] = otc_open
    result['otc_quote_date'] = otc_quote_date.strftime('%Y-%m-%d')
    result['lookup'] = stats

    return result

if __name__ == '__main__':
    print(itm_stats(14.510, 1.156))
