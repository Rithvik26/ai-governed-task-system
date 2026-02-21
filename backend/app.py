import logging
import time

from flask import Flask, g, request

from config import Config
from database import db
from errors import register_error_handlers
from routes.projects import projects_bp
from routes.tasks import tasks_bp


def create_app(config_class=Config):
    """Application factory. Accepts a config class to support test overrides."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure root logger before anything else logs.
    logging.basicConfig(
        level=getattr(logging, app.config.get("LOG_LEVEL", "INFO")),
        format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
    )

    db.init_app(app)

    app.register_blueprint(projects_bp)
    app.register_blueprint(tasks_bp)

    register_error_handlers(app)

    # ------------------------------------------------------------------
    # Observability: log every request with method, path, status, latency
    # ------------------------------------------------------------------

    @app.before_request
    def _record_start_time():
        g.start_time = time.monotonic()

    @app.after_request
    def _log_request(response):
        duration_ms = (time.monotonic() - g.start_time) * 1000
        logging.getLogger("request").info(
            "%s %s  →  %d  (%.1f ms)",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )
        return response

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(debug=False, host="127.0.0.1", port=5001)
