import pytest
import tempfile
import os
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import SqliteDatabase, get_db


@pytest.fixture(autouse=True)
def isolated_test_db():
    # Use isolated temp database for each test so tavli.db is never touched
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = f.name
    test_db = SqliteDatabase(db_path=temp_path)
    app.dependency_overrides[get_db] = lambda: test_db
    yield test_db
    app.dependency_overrides.pop(get_db, None)
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.mark.asyncio
async def test_create_and_get_event():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create Event
        payload = {
            "title": "Roadtrip 2026",
            "baseCurrency": "EUR",
            "creatorName": "Alice",
            "initialParticipants": ["Bob", "Charlie"]
        }
        res = await client.post("/api/events", json=payload)
        assert res.status_code in (200, 201)
        data = res.json()
        assert data["title"] == "Roadtrip 2026"
        assert data["baseCurrency"] == "EUR"
        assert len(data["participants"]) == 3
        event_id = data["id"]

        # 2. Get Event
        get_res = await client.get(f"/api/events/{event_id}")
        assert get_res.status_code == 200
        get_data = get_res.json()
        assert get_data["id"] == event_id
        assert len(get_data["participants"]) == 3


@pytest.mark.asyncio
async def test_get_nonexistent_event():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/events/nonexistent-123")
        assert res.status_code == 404
        assert "not found" in res.json()["message"].lower()


@pytest.mark.asyncio
async def test_add_participant():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_res = await client.post("/api/events", json={
            "title": "Camp 2026",
            "baseCurrency": "USD",
            "creatorName": "Alice",
            "initialParticipants": []
        })
        event_id = create_res.json()["id"]

        # Add participant
        part_res = await client.post(f"/api/events/{event_id}/participants", json={"name": "David"})
        assert part_res.status_code in (200, 201)
        part = part_res.json()
        assert part["name"] == "David"
        assert part["eventId"] == event_id

        # Verify participant appears in event
        event_res = await client.get(f"/api/events/{event_id}")
        assert any(p["name"] == "David" for p in event_res.json()["participants"])


@pytest.mark.asyncio
async def test_create_and_delete_expense():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_res = await client.post("/api/events", json={
            "title": "Dinner Event",
            "baseCurrency": "EUR",
            "creatorName": "Alice",
            "initialParticipants": ["Bob"]
        })
        event = create_res.json()
        event_id = event["id"]
        alice_id = next(p["id"] for p in event["participants"] if p["name"] == "Alice")
        bob_id = next(p["id"] for p in event["participants"] if p["name"] == "Bob")

        # Create Expense (Equal Split)
        exp_payload = {
            "eventId": event_id,
            "payerId": alice_id,
            "description": "Tapas & Sangria",
            "originalAmount": 50.0,
            "originalCurrency": "EUR",
            "isItemized": False,
            "splitType": "EQUAL",
            "splits": [
                {"participantId": alice_id},
                {"participantId": bob_id}
            ]
        }
        exp_res = await client.post(f"/api/events/{event_id}/expenses", json=exp_payload)
        assert exp_res.status_code in (200, 201)
        exp = exp_res.json()
        assert exp["description"] == "Tapas & Sangria"
        assert exp["baseAmount"] == 50.0
        assert len(exp["splits"]) == 2
        assert exp["splits"][0]["computedBaseAmount"] == 25.0
        assert exp["splits"][1]["computedBaseAmount"] == 25.0
        expense_id = exp["id"]

        # Delete Expense
        del_res = await client.request(
            "DELETE",
            f"/api/events/{event_id}/expenses/{expense_id}",
            json={"actorId": alice_id}
        )
        assert del_res.status_code in (200, 204)

        # Verify expense is gone
        event_res = await client.get(f"/api/events/{event_id}")
        assert len(event_res.json()["expenses"]) == 0


@pytest.mark.asyncio
async def test_create_settlement():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_res = await client.post("/api/events", json={
            "title": "Settlement Event",
            "baseCurrency": "EUR",
            "creatorName": "Alice",
            "initialParticipants": ["Bob"]
        })
        event = create_res.json()
        event_id = event["id"]
        alice_id = next(p["id"] for p in event["participants"] if p["name"] == "Alice")
        bob_id = next(p["id"] for p in event["participants"] if p["name"] == "Bob")

        # Settlement payload
        set_payload = {
            "eventId": event_id,
            "fromParticipantId": bob_id,
            "toParticipantId": alice_id,
            "amount": 25.0,
            "currency": "EUR"
        }
        set_res = await client.post(f"/api/events/{event_id}/settlements", json=set_payload)
        assert set_res.status_code in (200, 201)
        settlement = set_res.json()
        assert settlement["amount"] == 25.0
        assert settlement["fromParticipantId"] == bob_id

        # Verify settlement in event data
        event_res = await client.get(f"/api/events/{event_id}")
        assert len(event_res.json()["settlements"]) == 1


@pytest.mark.asyncio
async def test_exchange_rates():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/exchange-rates?from=USD&to=EUR")
        assert res.status_code == 200
        data = res.json()
        assert "rate" in data
        assert "date" in data
        assert data["rate"] > 0


@pytest.mark.asyncio
async def test_update_expense():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_res = await client.post("/api/events", json={
            "title": "Update Test",
            "baseCurrency": "EUR",
            "creatorName": "Alice",
            "initialParticipants": ["Bob"]
        })
        event = create_res.json()
        event_id = event["id"]
        alice_id = next(p["id"] for p in event["participants"] if p["name"] == "Alice")
        bob_id = next(p["id"] for p in event["participants"] if p["name"] == "Bob")

        # Create
        exp_res = await client.post(f"/api/events/{event_id}/expenses", json={
            "eventId": event_id,
            "payerId": alice_id,
            "description": "Lunch",
            "originalAmount": 30.0,
            "originalCurrency": "EUR",
            "isItemized": False,
            "splitType": "EQUAL",
            "splits": [{"participantId": alice_id}, {"participantId": bob_id}]
        })
        expense_id = exp_res.json()["id"]

        # Update
        update_res = await client.put(f"/api/expenses/{expense_id}", json={
            "description": "Lunch with Dessert",
            "originalAmount": 40.0,
            "originalCurrency": "EUR",
            "splits": [{"participantId": alice_id}, {"participantId": bob_id}]
        })
        assert update_res.status_code == 200
        updated = update_res.json()
        assert updated["description"] == "Lunch with Dessert"
        assert updated["baseAmount"] == 40.0
        assert updated["splits"][0]["computedBaseAmount"] == 20.0


@pytest.mark.asyncio
async def test_itemized_expense_creation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_res = await client.post("/api/events", json={
            "title": "Itemized Dinner",
            "baseCurrency": "EUR",
            "creatorName": "Alice",
            "initialParticipants": ["Bob"]
        })
        event = create_res.json()
        event_id = event["id"]
        alice_id = next(p["id"] for p in event["participants"] if p["name"] == "Alice")
        bob_id = next(p["id"] for p in event["participants"] if p["name"] == "Bob")

        # Create Itemized Expense:
        # Item 1: Burger 10 (Alice)
        # Item 2: Pizza 20 (Bob)
        # Item 3: Wine 10 (Alice & Bob -> 5 each)
        # Subtotal: 40, Tax: 4 (10%), Tip: 0
        exp_res = await client.post(f"/api/events/{event_id}/expenses", json={
            "eventId": event_id,
            "payerId": alice_id,
            "description": "Dinner with receipt",
            "originalAmount": 44.0,
            "originalCurrency": "EUR",
            "isItemized": True,
            "lineItems": [
                {"title": "Burger", "amount": 10.0, "consumerIds": [alice_id]},
                {"title": "Pizza", "amount": 20.0, "consumerIds": [bob_id]},
                {"title": "Wine", "amount": 10.0, "consumerIds": [alice_id, bob_id]},
            ],
            "taxAmount": 4.0,
            "tipAmount": 0.0
        })
        assert exp_res.status_code in (200, 201)
        exp = exp_res.json()
        assert exp["isItemized"] is True
        assert len(exp["lineItems"]) == 3

        # Alice: 10 + 5 = 15 subtotal (37.5%) -> 15 + 1.5 tax = 16.5
        # Bob: 20 + 5 = 25 subtotal (62.5%) -> 25 + 2.5 tax = 27.5
        alice_split = next(s for s in exp["splits"] if s["participantId"] == alice_id)
        bob_split = next(s for s in exp["splits"] if s["participantId"] == bob_id)
        assert alice_split["computedBaseAmount"] == 16.5
        assert bob_split["computedBaseAmount"] == 27.5


@pytest.mark.asyncio
async def test_health_probes():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        live = await client.get("/api/health/live")
        assert live.status_code == 200
        assert live.json() == {"status": "ok"}

        ready = await client.get("/api/health/ready")
        assert ready.status_code == 200
        assert ready.json() == {"status": "ready"}


@pytest.mark.asyncio
async def test_update_expense_exact_split():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_res = await client.post("/api/events", json={
            "title": "Exact Split Update Test",
            "baseCurrency": "EUR",
            "creatorName": "Alice",
            "initialParticipants": ["Bob"]
        })
        event = create_res.json()
        event_id = event["id"]
        alice_id = next(p["id"] for p in event["participants"] if p["name"] == "Alice")
        bob_id = next(p["id"] for p in event["participants"] if p["name"] == "Bob")

        # Create initially as equal
        exp_res = await client.post(f"/api/events/{event_id}/expenses", json={
            "eventId": event_id,
            "payerId": alice_id,
            "description": "Taxi",
            "originalAmount": 30.0,
            "originalCurrency": "EUR",
            "isItemized": False,
            "splitType": "EQUAL",
            "splits": [{"participantId": alice_id}, {"participantId": bob_id}]
        })
        expense_id = exp_res.json()["id"]

        # Update to EXACT split (Alice: 10 EUR, Bob: 20 EUR)
        update_res = await client.put(f"/api/expenses/{expense_id}", json={
            "description": "Taxi (Exact)",
            "originalAmount": 30.0,
            "originalCurrency": "EUR",
            "splitType": "EXACT",
            "splits": [
                {"participantId": alice_id, "amount": 10.0},
                {"participantId": bob_id, "amount": 20.0}
            ]
        })
        assert update_res.status_code == 200
        updated = update_res.json()
        alice_sp = next(s for s in updated["splits"] if s["participantId"] == alice_id)
        bob_sp = next(s for s in updated["splits"] if s["participantId"] == bob_id)
        assert alice_sp["computedBaseAmount"] == 10.0
        assert bob_sp["computedBaseAmount"] == 20.0


@pytest.mark.asyncio
async def test_multicurrency_expense_and_rate_conversion():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create event with base currency EUR
        create_res = await client.post("/api/events", json={
            "title": "US Trip",
            "baseCurrency": "EUR",
            "creatorName": "Alice",
            "initialParticipants": ["Bob"]
        })
        event = create_res.json()
        event_id = event["id"]
        alice_id = next(p["id"] for p in event["participants"] if p["name"] == "Alice")
        bob_id = next(p["id"] for p in event["participants"] if p["name"] == "Bob")

        # Create expense in USD: 100 USD (USD -> EUR rate is 0.92) -> baseAmount = 92.0 EUR
        exp_res = await client.post(f"/api/events/{event_id}/expenses", json={
            "eventId": event_id,
            "payerId": alice_id,
            "description": "Hotel NYC",
            "originalAmount": 100.0,
            "originalCurrency": "USD",
            "isItemized": False,
            "splitType": "EQUAL",
            "splits": [{"participantId": alice_id}, {"participantId": bob_id}]
        })
        assert exp_res.status_code in (200, 201)
        exp = exp_res.json()
        assert exp["originalAmount"] == 100.0
        assert exp["originalCurrency"] == "USD"
        assert exp["baseAmount"] == 92.0
        assert exp["exchangeRate"] == 0.92
        assert exp["splits"][0]["computedBaseAmount"] == 46.0
        assert exp["splits"][1]["computedBaseAmount"] == 46.0


@pytest.mark.asyncio
async def test_not_found_handling():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Non-existent expense update
        res = await client.put("/api/expenses/nonexistent-999", json={
            "description": "Ghost",
            "originalAmount": 10.0,
        })
        assert res.status_code == 404
        assert "not found" in res.json()["message"].lower()

        # Non-existent expense delete
        del_res = await client.request(
            "DELETE",
            "/api/events/ev-123/expenses/exp-999",
            json={"actorId": "p-1"}
        )
        assert del_res.status_code == 404
        assert "not found" in del_res.json()["message"].lower()


