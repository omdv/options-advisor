"""
Produce HTML report for the given data
using jinja2 template
"""

import os
from jinja2 import Environment, FileSystemLoader

# Define the templates directory
templates_dir = os.path.dirname(os.path.abspath(__file__))
j2_env = Environment(loader=FileSystemLoader(templates_dir), trim_blocks=True)

# Load the template
template = j2_env.get_template('report.html')

# Define the data for the report
data = {
    'title': 'My Report',
    'content': 'This is the content of my report.'
}

# Render the template with the data
html_report = template.render(data=data)

# Write the HTML report to a file
with open('report.html', 'w') as f:
    f.write(html_report)