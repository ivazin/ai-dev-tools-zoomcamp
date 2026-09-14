import pytest
from starlette.testclient import TestClient
from app.main import app
from app.database import SqliteDatabase, get_db
import tempfile
import os


@pytest.fixture
def test_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = f.name
    db = SqliteDatabase(db_path=temp_path)
    app.dependency_overrides[get_db] = lambda: db
    yield db
    app.dependency_overrides.pop(get_db, None)
    if os.path.exists(temp_path):
        os.remove(temp_path)


def test_websocket_join_and_presence(test_db):
    client = TestClient(app)
    # 1. Create an event
    res = client.post("/api/events", json={
        "title": "WS Test Event",
        "baseCurrency": "EUR",
        "creatorName": "Alice",
        "initialParticipants": ["Bob"]
    })
    assert res.status_code == 201
    event = res.json()
    event_id = event["id"]
    alice_id = next(p["id"] for p in event["participants"] if p["name"] == "Alice")

    # 2. Connect via WebSocket and send JOIN
    with client.websocket_connect(f"/ws/events/{event_id}") as websocket:
        websocket.send_json({"type": "JOIN", "participantId": alice_id})
        data = websocket.receive_json()

        assert data["type"] == "PRESENCE_CHANGE"
        assert "onlineParticipants" in data["payload"]
        assert alice_id in data["payload"]["onlineParticipants"]


def test_websocket_mutation_broadcast(test_db):
    client = TestClient(app)
    # 1. Create event
    res = client.post("/api/events", json={
        "title": "Broadcast Test",
        "baseCurrency": "EUR",
        "creatorName": "Alice",
        "initialParticipants": ["Bob"]
    })
    event = res.json()
    event_id = event["id"]
    alice_id = next(p["id"] for p in event["participants"] if p["name"] == "Alice")

    # 2. Connect client to WebSocket room
    with client.websocket_connect(f"/ws/events/{event_id}") as websocket:
        websocket.send_json({"type": "JOIN", "participantId": alice_id})
        presence = websocket.receive_json()
        assert presence["type"] == "PRESENCE_CHANGE"

        # 3. Add participant via REST API
        add_res = client.post(f"/api/events/{event_id}/participants", json={"name": "Charlie"})
        assert add_res.status_code == 201
        new_p = add_res.json()

        # 4. WebSocket should receive PARTICIPANT_ADDED
        msg = websocket.receive_json()
        assert msg["type"] == "PARTICIPANT_ADDED"
        assert msg["payload"]["name"] == "Charlie"
        assert msg["actorId"] == new_p["id"]

        # 5. Create expense via REST API
        exp_res = client.post(f"/api/events/{event_id}/expenses", json={
            "eventId": event_id,
            "payerId": alice_id,
            "description": "Coffee",
            "originalAmount": 6.0,
            "originalCurrency": "EUR",
            "isItemized": False,
            "splitType": "EQUAL",
            "splits": [{"participantId": alice_id}]
        })
        assert exp_res.status_code == 201

        # 6. WebSocket should receive EXPENSE_CREATED
        exp_msg = websocket.receive_json()
        assert exp_msg["type"] == "EXPENSE_CREATED"
        assert exp_msg["payload"]["description"] == "Coffee"
        assert exp_msg["actorId"] == alice_id
