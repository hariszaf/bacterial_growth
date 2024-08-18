from flask import Flask
import flask_app.app.views as views


def create_app():
    app = Flask(__name__)

    app.config.update(
        DEBUG=True,
        TEMPLATES_AUTO_RELOAD=True,
        EXPLAIN_TEMPLATE_LOADING=True,
    )

    app.add_url_rule("/",          view_func=views.index_page)
    app.add_url_rule("/search",    view_func=views.search_page)
    app.add_url_rule("/dashboard", view_func=views.dashboard_page)
    app.add_url_rule("/upload",    view_func=views.upload_page)
    app.add_url_rule("/help",      view_func=views.help_page)
    app.add_url_rule("/about",     view_func=views.about_page)

    return app


if __name__ == "__main__":
    app = create_app()

    app.run(host="0.0.0.0", port=8080)
