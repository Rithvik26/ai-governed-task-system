import logging
import traceback

from flask import jsonify

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base class for all application errors. Subclasses set status_code and code."""

    status_code = 500
    code = "INTERNAL_ERROR"

    def __init__(self, message, code=None, status_code=None):
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"


class ValidationError(AppError):
    status_code = 400
    code = "VALIDATION_ERROR"


class StateTransitionError(AppError):
    """Raised by Task.transition_to() when a move between statuses is not allowed."""

    status_code = 400
    code = "INVALID_STATUS_TRANSITION"

    def __init__(self, from_status, to_status):
        message = (
            f"Cannot transition from '{from_status.value}' to '{to_status.value}'"
        )
        super().__init__(message)


def _error_body(message, code):
    return jsonify({"error": message, "code": code})


def register_error_handlers(app):
    """Attach handlers for AppError subclasses and uncaught exceptions."""

    @app.errorhandler(AppError)
    def handle_app_error(exc):
        if exc.status_code >= 500:
            logger.error("Application error: %s [%s]", exc.message, exc.code)
        else:
            logger.warning("Application error: %s [%s]", exc.message, exc.code)
        return _error_body(exc.message, exc.code), exc.status_code

    @app.errorhandler(Exception)
    def handle_unhandled(exc):
        logger.error(
            "Unhandled exception: %s\n%s", str(exc), traceback.format_exc()
        )
        return _error_body("An unexpected error occurred", "INTERNAL_ERROR"), 500
