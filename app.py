import os

from flask import Flask, render_template

from config import Config
from extensions import db, login_manager, mail


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprints -- one per module, matches the project's module breakdown
    from routes.auth import auth_bp
    from routes.property_routes import property_bp
    from routes.document_routes import document_bp
    from routes.verification_routes import verification_bp
    from routes.admin_routes import admin_bp
    from routes.analysis_routes import analysis_bp
    from routes.photo_routes import photo_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(property_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(verification_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(photo_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/how-it-works")
    def how_it_works():
        return render_template("how_it_works.html")

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("403.html"), 403

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
