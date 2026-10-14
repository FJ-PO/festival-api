from app.models import UserRole

API = "/api/v1"


def setup_festival(client, headers) -> tuple[int, int]:
    venue = client.post(
        f"{API}/venues",
        json={"name": "Recinto Ferial", "address": "s/n", "municipality": "Algeciras", "capacity": 5000},
        headers=headers,
    ).json()
    fest = client.post(
        f"{API}/festivals",
        json={"name": "Bahía Test Fest", "start_date": "2099-07-01", "end_date": "2099-07-02", "venue_id": venue["id"]},
        headers=headers,
    )
    assert fest.status_code == 201, fest.text
    fid = fest.json()["id"]
    tt = client.post(
        f"{API}/festivals/{fid}/ticket-types",
        json={"name": "General", "price": "50.00", "quantity_total": 5, "max_per_order": 4},
        headers=headers,
    ).json()
    assert client.post(f"{API}/festivals/{fid}/publish", headers=headers).status_code == 200
    return fid, tt["id"]


def test_register_and_login(client, login):
    r = client.post(f"{API}/auth/register", json={"email": "Ana@Example.com", "full_name": "Ana", "password": "Password123"})
    assert r.status_code == 201
    assert r.json()["role"] == "customer"
    headers = login("ana@example.com")
    assert client.get(f"{API}/auth/me", headers=headers).json()["email"] == "ana@example.com"


def test_customer_cannot_create_festival(client, make_user, login):
    make_user(UserRole.CUSTOMER)
    r = client.post(f"{API}/venues", json={"name": "X", "address": "x", "municipality": "Tarifa", "capacity": 1},
                    headers=login("customer@example.com"))
    assert r.status_code == 403


def test_invalid_municipality(client, make_user, login):
    make_user(UserRole.ORGANIZER)
    r = client.post(f"{API}/venues", json={"name": "X", "address": "x", "municipality": "Sevilla", "capacity": 1},
                    headers=login("organizer@example.com"))
    assert r.status_code == 422


def test_full_purchase_and_checkin_flow(client, make_user, login):
    make_user(UserRole.ORGANIZER)
    make_user(UserRole.CUSTOMER)
    make_user(UserRole.STAFF)
    make_user(UserRole.CUSTOMER, email="amigo@example.com")
    org, cust, staff = login("organizer@example.com"), login("customer@example.com"), login("staff@example.com")

    fid, ttid = setup_festival(client, org)
    client.post(f"{API}/festivals/{fid}/discount-codes", json={"code": "campo10", "percent_off": 10}, headers=org)

    # Catálogo público filtrado por municipio
    listing = client.get(f"{API}/festivals", params={"municipality": "Algeciras"}).json()
    assert listing["total"] == 1
    assert client.get(f"{API}/festivals", params={"municipality": "Tarifa"}).json()["total"] == 0

    # Pedido con descuento
    r = client.post(f"{API}/orders", json={"festival_id": fid, "items": [{"ticket_type_id": ttid, "quantity": 2}],
                                          "discount_code": "CAMPO10"}, headers=cust)
    assert r.status_code == 201, r.text
    order = r.json()
    assert order["status"] == "pending" and order["total"] == "90.00"

    # Stock reservado
    tts = client.get(f"{API}/festivals/{fid}/ticket-types").json()
    assert tts[0]["quantity_available"] == 3

    # Pago rechazado y luego aceptado
    assert client.post(f"{API}/orders/{order['id']}/pay", json={"card_number": "4000000000000000"}, headers=cust).status_code == 402
    paid = client.post(f"{API}/orders/{order['id']}/pay", json={"card_number": "4111111111111111"}, headers=cust)
    assert paid.json()["status"] == "paid"

    tickets = client.get(f"{API}/tickets", headers=cust).json()["items"]
    assert len(tickets) == 2

    # Transferencia: el código cambia
    t0 = tickets[0]
    moved = client.post(f"{API}/tickets/{t0['id']}/transfer", json={"email": "amigo@example.com"}, headers=cust).json()
    assert moved["code"] != t0["code"]
    assert client.post(f"{API}/checkin", json={"code": t0["code"]}, headers=staff).json()["reason"] == "not_found"

    # Control de acceso
    ok = client.post(f"{API}/checkin", json={"code": moved["code"], "festival_id": fid}, headers=staff).json()
    assert ok["accepted"] is True
    again = client.post(f"{API}/checkin", json={"code": moved["code"]}, headers=staff).json()
    assert again["accepted"] is False and again["reason"] == "already_used"
    assert client.post(f"{API}/checkin", json={"code": moved["code"]}, headers=cust).status_code == 403

    stats = client.get(f"{API}/festivals/{fid}/stats", headers=org).json()
    assert stats["revenue"] == "90.00"
    assert stats["tickets_issued"] == 2 and stats["tickets_checked_in"] == 1

    # Con una entrada usada no se puede reembolsar
    assert client.post(f"{API}/orders/{order['id']}/cancel", headers=cust).status_code == 409


def test_stock_limits_and_cancel_releases(client, make_user, login):
    make_user(UserRole.ORGANIZER)
    make_user(UserRole.CUSTOMER)
    org, cust = login("organizer@example.com"), login("customer@example.com")
    fid, ttid = setup_festival(client, org)

    too_many = client.post(f"{API}/orders", json={"festival_id": fid, "items": [{"ticket_type_id": ttid, "quantity": 6}]}, headers=cust)
    assert too_many.status_code == 409

    o1 = client.post(f"{API}/orders", json={"festival_id": fid, "items": [{"ticket_type_id": ttid, "quantity": 4}]}, headers=cust).json()
    sold_out = client.post(f"{API}/orders", json={"festival_id": fid, "items": [{"ticket_type_id": ttid, "quantity": 2}]}, headers=cust)
    assert sold_out.status_code == 409

    assert client.post(f"{API}/orders/{o1['id']}/cancel", headers=cust).json()["status"] == "cancelled"
    assert client.get(f"{API}/festivals/{fid}/ticket-types").json()[0]["quantity_available"] == 5


def test_cancel_festival_refunds_orders(client, make_user, login):
    make_user(UserRole.ORGANIZER)
    make_user(UserRole.CUSTOMER)
    org, cust = login("organizer@example.com"), login("customer@example.com")
    fid, ttid = setup_festival(client, org)
    o = client.post(f"{API}/orders", json={"festival_id": fid, "items": [{"ticket_type_id": ttid, "quantity": 1}]}, headers=cust).json()
    client.post(f"{API}/orders/{o['id']}/pay", json={}, headers=cust)

    assert client.post(f"{API}/festivals/{fid}/cancel", headers=org).json()["status"] == "cancelled"
    assert client.get(f"{API}/orders/{o['id']}", headers=cust).json()["status"] == "refunded"
    assert client.get(f"{API}/tickets", headers=cust).json()["items"][0]["status"] == "cancelled"


def test_draft_hidden_from_public(client, make_user, login):
    make_user(UserRole.ORGANIZER)
    org = login("organizer@example.com")
    venue = client.post(f"{API}/venues", json={"name": "Castillo", "address": "x", "municipality": "Jimena de la Frontera", "capacity": 100}, headers=org).json()
    r = client.post(f"{API}/festivals", json={"name": "Borrador", "start_date": "2099-01-01", "end_date": "2099-01-01", "venue_id": venue["id"]}, headers=org)
    assert r.status_code == 201, r.text
    fid = r.json()["id"]
    assert client.get(f"{API}/festivals/{fid}").status_code == 404
    assert client.get(f"{API}/festivals/{fid}", headers=org).status_code == 200
    # No se publica sin tipos de entrada
    assert client.post(f"{API}/festivals/{fid}/publish", headers=org).status_code == 409
