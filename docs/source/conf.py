# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

from packflow import __version__

project = "Packflow"
copyright = "2026 U.S. Federal Government (in countries where recognized)"
author = "CDAO Models as a Service"

version = __version__
release = __version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosectionlabel",
    "sphinx_autodoc_typehints",
    "sphinx_multiversion",
    "sphinx_click",
    "nbsphinx",
    "sphinxcontrib.autodoc_pydantic",
    "sphinx_favicon",
]

templates_path = ["_templates"]
exclude_patterns = ["api-reference/auto/modules.rst"]
# Prevent duplicate label warnings from autosectionlabel
autosectionlabel_prefix_document = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_context = {
    "versions": [
        {"name": "Latest", "url": "/main"}
    ]
}
html_css_files = [
    "custom.css",
]
html_theme_options = {"navigation_depth": 5, "collapse_navigation": True}

# Icons/logo for tab and sidebar
favicons = ["packflow-logo-16px.png", "packflow-logo-32px.png"]

# -- Options for Multiversion Extension
# exclude -alpha and -beta for now
smv_tag_whitelist = (
    r"^v\d+\.\d+$"  # only include tags with semver v + version, e.g., v0.1.0
)
smv_branch_whitelist = r"^main$"  # only include the 'main' branch
smv_remote_whitelist = r"^origin$"
smv_released_pattern = r"^tags/v\d+\.\d+$"
smv_outputdir_format = "{ref.name}"
