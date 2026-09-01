# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Ai4Bio'
copyright = '2026, Masha Zamani'
author = 'Masha Zamani'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
import os
import sys

# Add my project root to the system path so Sphinx can find my modules
sys.path.insert(0, os.path.abspath('../..'))

# Add extensions for parsing docstrings and linking to source code
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon', 
    'sphinx.ext.viewcode',
]

# Set the HTML theme to Read the Docs
html_theme = 'sphinx_rtd_theme'