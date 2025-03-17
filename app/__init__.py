from flask import Flask
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY')

    # Register the main blueprint
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    # Register the authentication blueprint
    from .auth import auth_bp
    app.register_blueprint(auth_bp)


    return app
