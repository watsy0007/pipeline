# Automatically created by: scrapyd-deploy

from setuptools import setup, find_packages

setup(
    name         = 'project',
    version      = '1.26',
    packages     = find_packages(),
    include_package_data = True,
    entry_points = {'scrapy': ['settings = pipeline.settings']},
)
