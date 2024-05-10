"""
Standalone renderer of jinja2 template
template: report.html
context: api_itm(), api_vol()
"""
from jinja2 import Template
from api_itm import api_itm
from api_vol import api_vol
from io_utils import save_to_s3, read_from_s3


def handler():
    """
    Render a jinja2 template
    """
    template = read_from_s3('templates/report.html')

    template = Template(template)
    context = {'itm': api_itm(), 'vol': api_vol()}

    rendered_template = template.render(context)
    save_to_s3(rendered_template, 'index.html')

    return rendered_template
