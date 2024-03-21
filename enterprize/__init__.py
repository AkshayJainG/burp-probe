from flask import Flask
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_smorest import Api
from enterprize.helpers import render_partial

db = SQLAlchemy()
bcrypt = Bcrypt()
api = Api()

def create_app(config):

    app = Flask(__name__, static_url_path='')
    app.config.from_object('enterprize.config.{}'.format(config.title()))
    app.logger.info(f"Burp Enterprize starting in {config} mode.")

    app.config["API_TITLE"] = "Test REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.1.0"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    db.init_app(app)
    bcrypt.init_app(app)
    api.init_app(app)

    def finalize(arg):
        if arg is None:
            return ''
        return arg

    # converts None types to empty strings in the template context
    app.jinja_env.finalize = finalize
    # clean up white space left behind by jinja template code
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    app.add_template_global(render_partial)

    from enterprize.views.core import blp as CoreBlueprint
    app.register_blueprint(CoreBlueprint)

    from enterprize.views.api import blp as ApiBlueprint
    api.register_blueprint(ApiBlueprint, url_prefix='/api')

    @app.cli.command("init")
    def init_data():
        from enterprize import models
        db.create_all()
        # initialization logic here (optional)
        app.logger.info('Database initialized.')

    @app.cli.command("migrate")
    def migrate_data():
        # migration logic here
        app.logger.info('Migration complete.')

    return app
