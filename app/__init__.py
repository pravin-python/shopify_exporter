from flask import Flask
from config import Config
from app.extensions import db

def create_app(config_class=Config):
    """Application factory for creating Flask app instances."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    
    # Initialize Flask extensions
    db.init_app(app)
    
    with app.app_context():
        # Register blueprints
        from app.routes.dashboard import dashboard_bp
        from app.routes.sync import sync_bp
        from app.routes.export import export_bp
        from app.routes.api import api_bp
        from app.routes.auth import auth_bp
        
        app.register_blueprint(dashboard_bp)
        app.register_blueprint(sync_bp, url_prefix='/sync')
        app.register_blueprint(export_bp, url_prefix='/export')
        app.register_blueprint(api_bp, url_prefix='/api')
        app.register_blueprint(auth_bp, url_prefix='/auth')
        
    return app
