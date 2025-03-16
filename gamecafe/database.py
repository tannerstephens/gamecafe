from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

SQLALCHEMY_DATABASE_URI_KEY = "SQLALCHEMY_DATABASE_URI"


class Database:
    def __init__(self, app: Flask | None = None) -> None:
        self.Base = declarative_base()

        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        self.engine = create_engine(app.config.get(SQLALCHEMY_DATABASE_URI_KEY))
        self.session = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        )

        self.Base.query = self.session.query_property()

        @app.teardown_appcontext
        def shutdown_session(exception=None):
            self.session.remove()


db = Database()
