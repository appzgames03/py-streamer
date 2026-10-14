"""Flask application factory for pyst.

Constructs and configures the Flask application. This pattern keeps the
app modular, easily testable with mock configs, and free of global state.
"""

from typing import Any, Mapping
from flask import Flask, render_template


def create_app(config: Mapping[str, Any] | None = None) -> Flask:
    """Create and configure the Flask app.

    Args:
        config: Optional configuration dictionary (e.g. for testing).

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)

    # Default settings
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    if config:
        app.config.update(config)

    # Register blueprints
    from pyst.server.browse import browse_bp
    from pyst.server.streaming import streaming_bp
    from pyst.server.sync import root_sync_bp, sync_bp
    from pyst.server.upload import upload_bp

    app.register_blueprint(browse_bp)
    app.register_blueprint(streaming_bp)
    app.register_blueprint(sync_bp)
    app.register_blueprint(root_sync_bp)
    app.register_blueprint(upload_bp)

    # Register custom error handlers
    @app.errorhandler(403)
    def forbidden(error):
        return render_template(
            "base.html",
            content="<div style='text-align:center; padding:3rem;'><h2>403 Forbidden</h2><p>Access denied.</p><a href='/' class='btn'>Back to Dashboard</a></div>"
        ), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template(
            "base.html",
            content="<div style='text-align:center; padding:3rem;'><h2>404 Not Found</h2><p>The requested resource could not be found.</p><a href='/' class='btn'>Back to Dashboard</a></div>"
        ), 404

    return app
