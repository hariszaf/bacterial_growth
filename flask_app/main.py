# TODO only necessary while we dip into the streamlit structure
import sys
sys.path.append('src')

from flask import Flask
import flask_assets

import flask_app.app.pages.static as static_pages
import flask_app.app.pages.search as search_pages
import flask_app.app.pages.dashboard as dashboard_pages
import flask_app.app.pages.upload as upload_pages


def create_app():
    app = Flask(__name__)
    assets = flask_assets.Environment(app)

    javascripts = flask_assets.Bundle(
        'js/vendor/jquery-3.7.1.js',
        'js/main.js',
        filters='jsmin',
        output='build/bundle.js'
    )
    assets.register('js_bundle', javascripts)

    stylesheets = flask_assets.Bundle(
        'css/reset.css',
        'css/main.css',
        'css/sidebar.css',
        filters='cssmin',
        output='build/bundle.css'
    )
    assets.register('css_bundle', stylesheets)

    app.config.update(
        DEBUG=True,
        ASSETS_DEBUG=True,
        TEMPLATES_AUTO_RELOAD=True,
        EXPLAIN_TEMPLATE_LOADING=True,
        SECRET_KEY='development_key',
    )

    app.add_url_rule("/",      view_func=static_pages.home,  endpoint="static_home_page")
    app.add_url_rule("/help",  view_func=static_pages.help,  endpoint="static_help_page")
    app.add_url_rule("/about", view_func=static_pages.about, endpoint="static_about_page")

    app.add_url_rule("/dashboard", view_func=dashboard_pages.index, endpoint="dashboard_index_page")
    app.add_url_rule("/upload",    view_func=upload_pages.index,    endpoint="upload_index_page")

    app.add_url_rule(
        "/search",
        view_func=search_pages.index,
        endpoint="search_index_page",
        methods=["GET", "POST"],
    )

    return app


if __name__ == "__main__":
    app = create_app()

    app.run(host="0.0.0.0", port=8080)
