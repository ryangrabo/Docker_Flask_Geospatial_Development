from flask import Flask
from dotenv import load_dotenv
import os
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY')
    app.config['PREFERRED_URL_SCHEME'] = 'https'


    # Trust the X-Forwarded-* headers coming from Nginx
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Register the main blueprint
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    # Register the authentication blueprint
    from .auth import auth_bp
    app.register_blueprint(auth_bp)


    return app
