"""
Standalone renderer of jinja2 template
template: report.html
context: api_itm(), api_vol()
"""
import logging
import os
import sys
from datetime import datetime, timezone
from jinja2 import Environment

from api_itm import api_itm
from api_vol import api_vol
from api_garch import api_garch
from io_utils import save_to_s3, read_from_s3

# CloudWatch logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
logger.addHandler(stream_handler)

def get_config():
    """
    Get the configuration
    """
    config = {
        'mode': os.environ.get('MODE'),
        'bucket_name': os.environ.get('S3_BUCKET_NAME'),
        'pickle_path': os.environ.get('ITM_PICKLE_PATH'),
        'quotes_api_key': os.environ.get('QUOTES_API_KEY'),
    }
    logger.info("Config: %s", config)
    return config


def handler(event, context):
    """
    Lambda handler
    """
    logger.info("Starting...")
    cfg = get_config()

    def quote(value):
        """
        Formatter for quotes
        """
        return f"{value:,.2f}"

    # Create a new Jinja2 environment
    env = Environment()

    # Register the 'quote' filter
    env.filters['quote'] = quote

    # Read the template from S3
    template_source = read_from_s3(cfg, 'templates/report.html', decode=True)

    # Create the template
    template = env.from_string(template_source)
    logger.info("Template read from S3")

    itm_data = api_itm(cfg)
    logger.info("API ITM: %s", itm_data.keys())

    vol_data = api_vol(cfg)
    logger.info("API VOL: %s", vol_data.keys())

    garch_data = api_garch(cfg)
    logger.info("API GARCH: %s", garch_data.keys())

    context = {
        'timestamp': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'itm': itm_data,
        'vol': vol_data,
        'garch': garch_data
    }

    rendered_template = template.render(context)
    save_to_s3(
        cfg,
        'index.html',
        rendered_template,
        content_type='text/html'
    )

    logger.info("Rendered template saved to S3")
    return "Done"

if __name__ == "__main__":
    handler(None, None)
