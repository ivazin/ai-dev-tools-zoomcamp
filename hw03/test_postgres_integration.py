"""Integration coverage for the PostgreSQL deployment path."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient


POSTGRES_URL_PREFIX = "postgresql+psycopg://"

if not os.environ.get("RELAY_DATABASE_URL", "").startswith(POSTGRES_URL_PREFIX):
    pytestmark = pytest.mark.skip(reason="requires RELAY_DATABASE_URL pointing at PostgreSQL")

import main
from database import Base, Task, db_session, engine
from storage import claim_one


@pytest.fixture(autouse=True)
def empty_postgres_database():
    """Keep the disposable CI database isolated between test runs."""

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


def _register(client: TestClient, name: str) -> tuple[dict[str, str], dict[str, str]]:
    response = client.post("/api/v1/agents", json={"name": name})
    assert response.status_code == 201
    identity = response.json()
    return identity, {"Authorization": f"Bearer {identity['token']}"}


def test_postgresql_claims_use_row_locks_without_duplicate_delivery():
    assert engine.dialect.name == "postgresql"

    with TestClient(main.app) as client:
        _sender, sender_headers = _register(client, "sender")
        recipient, _recipient_headers = _register(client, "recipient")
        for number in range(12):
            response = client.post(
                "/api/v1/tasks",
                headers=sender_headers,
                json={"to": recipient["agent_id"], "input": f"postgres-task-{number}"},
            )
            assert response.status_code == 201

        with ThreadPoolExecutor(max_workers=12) as pool:
            claims = list(pool.map(lambda number: claim_one(recipient["agent_id"], f"pg-worker-{number}"), range(12)))

    assert all(claim is not None for claim in claims)
    task_ids = [claim["task_id"] for claim in claims if claim is not None]
    assert len(task_ids) == 12
    assert len(set(task_ids)) == 12
    with db_session() as db:
        assert db.query(Task).filter(Task.status == "processing").count() == 12
