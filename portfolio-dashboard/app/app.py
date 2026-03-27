"""
Flask App Factory - Portfolio Dashboard.
"""

import os
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from dotenv import load_dotenv

load_dotenv()


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "postgresql://portfolio:portfolio@localhost:5432/portfolio"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") == "production"

    # Extensions
    from models import db
    db.init_app(app)
    Migrate(app, db)

    CORS(app, origins=["https://dashboard.5ginvest.fr", "http://localhost:3000", "http://localhost:5051"],
         supports_credentials=True)

    # OAuth (optionnel — skip si pas configuré ou erreur d'import)
    try:
        from auth import auth_bp, init_oauth
        init_oauth(app)
        app.register_blueprint(auth_bp)
    except Exception as e:
        print(f"OAuth non chargé (mode solo): {e}")

    # Routes
    from routes import api
    app.register_blueprint(api)

    # Create tables on first run
    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
