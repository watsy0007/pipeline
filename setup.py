# Automatically created by: scrapyd-deploy

from setuptools import setup, find_packages

setup(
    name         = 'project',
    version      = '1.16',
    packages     = find_packages(),
    entry_points = {'scrapy': ['settings = pipeline.settings']},
)
