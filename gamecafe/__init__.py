from flask import Flask, render_template

from .database import db
from .model_json_provider import ModelJsonProvider
from .session import get_user
from .views import RoleView


def create_app(config="gamecafe.config.Config") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config)

    app.json = ModelJsonProvider(app)

    with app.app_context():
        from .commands import commands

        db.init_app(app)
        RoleView.register_all_subviews(app)
        app.register_blueprint(commands)

    @app.context_processor
    def inject_global_variables():
        return {"user": get_user()}

    @app.errorhandler(404)
    def not_found(e):
        return render_template("pages/404.jinja")

    print(app.url_map)

    return app
