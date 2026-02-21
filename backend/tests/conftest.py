import pytest

from app import create_app
from config import TestConfig
from database import db as _db


@pytest.fixture(scope="session")
def app():
    """One Flask application per test session, configured for in-memory SQLite."""
    return create_app(TestConfig)


@pytest.fixture(scope="function")
def db(app):
    """Fresh database for every test function — tables created, then dropped."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app, db):
    """Flask test client bound to a clean database."""
    return app.test_client()
