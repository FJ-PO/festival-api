"""Genera la colección y el entorno de Postman para Festival Tickets API.

Uso:
    python postman/generar_coleccion.py

Crea en esta carpeta:
    festival-api.postman_collection.json
    festival-api.local.postman_environment.json

La colección está pensada para ejecutarse de principio a fin con el Collection Runner
(o con Newman): cada petición guarda en variables los ids que necesitan las siguientes.
Requiere haber cargado los datos de ejemplo (`python seed.py --reset`).
"""

import json
import re
import uuid
from pathlib import Path

OUT = Path(__file__).parent
API = "{{baseUrl}}/api/v1"


# ---------- Helpers ----------


def js(*lines: str) -> list[str]:
    return [line for block in lines for line in block.strip("\n").split("\n")]


def status(code: int) -> str:
    return f'pm.test("Status {code}", () => pm.response.to.have.status({code}));'


def save(var: str, expr: str) -> str:
    return f'pm.collectionVariables.set("{var}", {expr});'


def req(name, method, path, *, token=None, body=None, form=None, query=None, tests=(), pre=(), desc=None):
    raw_url = f"{API}{path}" if path.startswith("/") else path
    url = {"raw": raw_url, "host": [raw_url.split("/")[0]], "path": [p for p in raw_url.split("/")[1:] if p]}
    if query:
        url["query"] = [{"key": k, "value": str(v)} for k, v in query.items()]
        url["raw"] += "?" + "&".join(f"{k}={v}" for k, v in query.items())

    request = {"method": method, "header": [], "url": url}
    if desc:
        request["description"] = desc
    request["auth"] = (
        {"type": "bearer", "bearer": [{"key": "token", "value": f"{{{{{token}}}}}", "type": "string"}]}
        if token
        else {"type": "noauth"}
    )
    if body is not None:
        request["header"].append({"key": "Content-Type", "value": "application/json"})
        raw = json.dumps(body, indent=2, ensure_ascii=False)
        raw = re.sub(r'"(\{\{\w+Id\}\})"', r"\1", raw)  # los ids viajan como números, no como texto
        request["body"] = {"mode": "raw", "raw": raw,
                           "options": {"raw": {"language": "json"}}}
    if form is not None:
        request["body"] = {"mode": "urlencoded",
                           "urlencoded": [{"key": k, "value": v, "type": "text"} for k, v in form.items()]}

    event = []
    if pre:
        event.append({"listen": "prerequest", "script": {"type": "text/javascript", "exec": js(*pre)}})
    if tests:
        event.append({"listen": "test", "script": {"type": "text/javascript", "exec": js(*tests)}})
    return {"name": name, "event": event, "request": request}


def folder(name, items, desc=None):
    f = {"name": name, "item": items}
    if desc:
        f["description"] = desc
    return f


def login(role: str) -> dict:
    return req(
        f"Login {role}", "POST", "/auth/login",
        form={"username": f"{role}@example.com", "password": "{{password}}"},
        tests=[status(200), f"""
const body = pm.response.json();
pm.test("Devuelve token bearer y rol {role}", () => {{
    pm.expect(body.token_type).to.eql("bearer");
    pm.expect(body.access_token).to.be.a("string");
    pm.expect(body.user.role).to.eql("{role}");
}});
{save(f"token_{role}", "body.access_token")}
"""],
    )


# ---------- Peticiones ----------

sistema = folder("00 · Sistema", [
    req("Health check", "GET", "{{baseUrl}}/health", tests=[status(200), """
pm.test("status ok", () => pm.expect(pm.response.json().status).to.eql("ok"));
"""], pre=["""
// Sufijo único por ejecución para que emails, códigos y nombres no colisionen
pm.collectionVariables.set("runId", Date.now().toString().slice(-8));
"""]),
])

auth = folder("01 · Autenticación", [
    login("admin"),
    login("organizer"),
    login("staff"),
    login("customer"),
    req("Login con contraseña incorrecta → 401", "POST", "/auth/login",
        form={"username": "customer@example.com", "password": "incorrecta"}, tests=[status(401)]),
    req("Registro de nuevo usuario", "POST", "/auth/register",
        body={"email": "nuevo{{runId}}@example.com", "full_name": "Usuario Nuevo", "password": "Password123"},
        tests=[status(201), """
const body = pm.response.json();
pm.test("Se registra como customer", () => pm.expect(body.role).to.eql("customer"));
pm.test("No expone la contraseña", () => pm.expect(body).to.not.have.property("hashed_password"));
""" + save("newUserId", "body.id") + "\n" + save("newUserEmail", "body.email")]),
    req("Registro con email duplicado → 409", "POST", "/auth/register",
        body={"email": "nuevo{{runId}}@example.com", "full_name": "Usuario Nuevo", "password": "Password123"},
        tests=[status(409)]),
    req("Registro con contraseña corta → 422", "POST", "/auth/register",
        body={"email": "corta{{runId}}@example.com", "full_name": "Corta", "password": "123"},
        tests=[status(422)]),
    req("Login nuevo usuario", "POST", "/auth/login",
        form={"username": "{{newUserEmail}}", "password": "Password123"},
        tests=[status(200), save("token_newuser", "pm.response.json().access_token")]),
    req("Mi perfil (GET /me)", "GET", "/auth/me", token="token_customer", tests=[status(200), """
pm.test("Email correcto", () => pm.expect(pm.response.json().email).to.eql("customer@example.com"));
"""]),
    req("Actualizar mi perfil (PATCH /me)", "PATCH", "/auth/me", token="token_newuser",
        body={"full_name": "Usuario Nuevo Editado"}, tests=[status(200), """
pm.test("Nombre actualizado", () => pm.expect(pm.response.json().full_name).to.eql("Usuario Nuevo Editado"));
"""]),
    req("Sin token → 401", "GET", "/auth/me", tests=[status(401)]),
])

usuarios = folder("02 · Usuarios (admin)", [
    req("Listar usuarios", "GET", "/users", token="token_admin", query={"limit": 50}, tests=[status(200), """
const body = pm.response.json();
pm.test("Respuesta paginada", () => pm.expect(body).to.have.keys("items", "total", "limit", "offset"));
"""]),
    req("Buscar usuario por texto", "GET", "/users", token="token_admin", query={"q": "nuevo{{runId}}"},
        tests=[status(200), 'pm.test("Encuentra 1", () => pm.expect(pm.response.json().total).to.eql(1));']),
    req("Cambiar rol de usuario", "PATCH", "/users/{{newUserId}}", token="token_admin",
        body={"role": "customer", "is_active": True}, tests=[status(200)]),
    req("Customer no puede listar usuarios → 403", "GET", "/users", token="token_customer", tests=[status(403)]),
])

recintos = folder("03 · Recintos", [
    req("Listar recintos (público)", "GET", "/venues", tests=[status(200)]),
    req("Filtrar por municipio", "GET", "/venues", query={"municipality": "Tarifa"}, tests=[status(200), """
pm.test("Todos en Tarifa", () => pm.response.json().items.forEach(v => pm.expect(v.municipality).to.eql("Tarifa")));
"""]),
    req("Municipios válidos", "GET", "/venues/municipalities", tests=[status(200), """
pm.test("7 municipios", () => pm.expect(pm.response.json()).to.have.lengthOf(7));
"""]),
    req("Crear recinto", "POST", "/venues", token="token_organizer",
        body={"name": "Parque de San Roque {{runId}}", "address": "Av. de los Descubrimientos s/n",
              "municipality": "San Roque", "capacity": 4000, "latitude": 36.21, "longitude": -5.39},
        tests=[status(201), save("venueId", "pm.response.json().id")]),
    req("Obtener recinto", "GET", "/venues/{{venueId}}", tests=[status(200)]),
    req("Actualizar recinto (admin)", "PATCH", "/venues/{{venueId}}", token="token_admin", body={"capacity": 4500},
        tests=[status(200), 'pm.test("Capacidad 4500", () => pm.expect(pm.response.json().capacity).to.eql(4500));']),
    req("Organizador no puede editar recintos → 403", "PATCH", "/venues/{{venueId}}", token="token_organizer",
        body={"capacity": 1}, tests=[status(403)]),
    req("Municipio fuera de la comarca → 422", "POST", "/venues", token="token_organizer",
        body={"name": "Recinto Sevilla", "address": "x", "municipality": "Sevilla", "capacity": 100},
        tests=[status(422)]),
    req("Customer no puede crear recinto → 403", "POST", "/venues", token="token_customer",
        body={"name": "Recinto X", "address": "x", "municipality": "Tarifa", "capacity": 100}, tests=[status(403)]),
    req("Recinto inexistente → 404", "GET", "/venues/999999", tests=[status(404)]),
])

artistas = folder("04 · Artistas", [
    req("Listar artistas", "GET", "/artists", tests=[status(200)]),
    req("Buscar por género", "GET", "/artists", query={"genre": "Electrónica"}, tests=[status(200)]),
    req("Crear artista", "POST", "/artists", token="token_organizer",
        body={"name": "Poniente Trío {{runId}}", "genre": "Jazz", "country": "España", "bio": "Trío de Algeciras"},
        tests=[status(201), save("artistId", "pm.response.json().id")]),
    req("Obtener artista", "GET", "/artists/{{artistId}}", tests=[status(200)]),
    req("Actualizar artista", "PATCH", "/artists/{{artistId}}", token="token_organizer",
        body={"genre": "Jazz fusión"}, tests=[status(200)]),
])

festivales = folder("05 · Festivales y tipos de entrada", [
    req("Catálogo público", "GET", "/festivals", tests=[status(200), """
pm.test("Solo publicados", () => pm.response.json().items.forEach(f => pm.expect(f.status).to.eql("published")));
"""]),
    req("Catálogo filtrado (municipio + fechas)", "GET", "/festivals",
        query={"municipality": "Tarifa", "date_from": "2027-01-01", "date_to": "2027-12-31"}, tests=[status(200)]),
    req("Crear festival (borrador)", "POST", "/festivals", token="token_organizer",
        body={"name": "Postman Fest {{runId}}", "description": "Festival creado desde Postman", "genre": "Jazz",
              "start_date": "2099-07-01", "end_date": "2099-07-02", "min_age": 16, "venue_id": "{{venueId}}"},
        tests=[status(201), """
const body = pm.response.json();
pm.test("Nace en borrador", () => pm.expect(body.status).to.eql("draft"));
""" + save("festivalId", "body.id") + "\n" + save("festivalSlug", "body.slug")]),
    req("Fechas incoherentes → 422", "POST", "/festivals", token="token_organizer",
        body={"name": "Mal Fest", "start_date": "2099-07-05", "end_date": "2099-07-01", "venue_id": "{{venueId}}"},
        tests=[status(422)]),
    req("Borrador no visible al público → 404", "GET", "/festivals/{{festivalId}}", tests=[status(404)]),
    req("Borrador visible para su organizador", "GET", "/festivals/{{festivalId}}", token="token_organizer",
        tests=[status(200)]),
    req("Mis festivales (manage)", "GET", "/festivals/manage", token="token_organizer", query={"status": "draft"},
        tests=[status(200)]),
    req("Publicar sin tipos de entrada → 409", "POST", "/festivals/{{festivalId}}/publish", token="token_organizer",
        tests=[status(409)]),
    req("Actualizar festival", "PATCH", "/festivals/{{festivalId}}", token="token_organizer",
        body={"description": "Descripción actualizada"}, tests=[status(200)]),
    req("Crear tipo de entrada", "POST", "/festivals/{{festivalId}}/ticket-types", token="token_organizer",
        body={"name": "General", "description": "Acceso 2 días", "price": "50.00", "quantity_total": 10,
              "max_per_order": 4},
        tests=[status(201), save("ticketTypeId", "pm.response.json().id")]),
    req("Crear tipo de entrada VIP", "POST", "/festivals/{{festivalId}}/ticket-types", token="token_organizer",
        body={"name": "VIP", "price": "120.00", "quantity_total": 5, "max_per_order": 2},
        tests=[status(201), save("ticketTypeVipId", "pm.response.json().id")]),
    req("Actualizar tipo de entrada", "PATCH", "/ticket-types/{{ticketTypeVipId}}", token="token_organizer",
        body={"price": "110.00"}, tests=[status(200)]),
    req("Publicar festival", "POST", "/festivals/{{festivalId}}/publish", token="token_organizer", tests=[status(200), """
pm.test("Publicado", () => pm.expect(pm.response.json().status).to.eql("published"));
"""]),
    req("Obtener festival (público)", "GET", "/festivals/{{festivalId}}", tests=[status(200)]),
    req("Obtener festival por slug", "GET", "/festivals/slug/{{festivalSlug}}", tests=[status(200)]),
    req("Listar tipos de entrada", "GET", "/festivals/{{festivalId}}/ticket-types", tests=[status(200), """
pm.test("2 tipos", () => pm.expect(pm.response.json()).to.have.lengthOf(2));
"""]),
])

cartel = folder("06 · Cartel", [
    req("Añadir actuación", "POST", "/festivals/{{festivalId}}/lineup", token="token_organizer",
        body={"artist_id": "{{artistId}}", "stage": "Principal",
              "start_time": "2099-07-01T22:00:00Z", "end_time": "2099-07-01T23:30:00Z"},
        tests=[status(201), save("performanceId", "pm.response.json().id")]),
    req("Actuación solapada → 409", "POST", "/festivals/{{festivalId}}/lineup", token="token_organizer",
        body={"artist_id": "{{artistId}}", "stage": "Principal",
              "start_time": "2099-07-01T23:00:00Z", "end_time": "2099-07-02T00:30:00Z"}, tests=[status(409)]),
    req("Actuación fuera de fechas → 422", "POST", "/festivals/{{festivalId}}/lineup", token="token_organizer",
        body={"artist_id": "{{artistId}}", "stage": "Secundario",
              "start_time": "2099-08-01T22:00:00Z", "end_time": "2099-08-01T23:00:00Z"}, tests=[status(422)]),
    req("Ver cartel", "GET", "/festivals/{{festivalId}}/lineup", tests=[status(200), """
pm.test("1 actuación", () => pm.expect(pm.response.json()).to.have.lengthOf(1));
"""]),
    req("Buscar festival por artista", "GET", "/festivals", query={"q": "Poniente Trío {{runId}}"}, tests=[status(200), """
pm.test("Encuentra el festival", () => pm.expect(pm.response.json().total).to.eql(1));
"""]),
])

descuentos = folder("07 · Códigos de descuento", [
    req("Crear código de descuento", "POST", "/festivals/{{festivalId}}/discount-codes", token="token_organizer",
        body={"code": "postman10", "percent_off": 10, "max_uses": 100},
        tests=[status(201), """
pm.test("Se guarda en mayúsculas", () => pm.expect(pm.response.json().code).to.eql("POSTMAN10"));
""" + save("discountId", "pm.response.json().id")]),
    req("Código duplicado → 409", "POST", "/festivals/{{festivalId}}/discount-codes", token="token_organizer",
        body={"code": "POSTMAN10", "percent_off": 20}, tests=[status(409)]),
    req("Listar códigos", "GET", "/festivals/{{festivalId}}/discount-codes", token="token_organizer",
        tests=[status(200)]),
    req("Comprobar código válido", "GET", "/festivals/{{festivalId}}/discount-codes/check",
        query={"code": "postman10"}, tests=[status(200), """
pm.test("10%", () => pm.expect(pm.response.json().percent_off).to.eql(10));
"""]),
    req("Comprobar código inexistente → 404", "GET", "/festivals/{{festivalId}}/discount-codes/check",
        query={"code": "NOEXISTE"}, tests=[status(404)]),
    req("Actualizar código", "PATCH", "/discount-codes/{{discountId}}", token="token_organizer",
        body={"max_uses": 50}, tests=[status(200)]),
])

pedidos = folder("08 · Pedidos y pago", [
    req("Crear pedido con descuento", "POST", "/orders", token="token_customer",
        body={"festival_id": "{{festivalId}}", "items": [{"ticket_type_id": "{{ticketTypeId}}", "quantity": 2}],
              "discount_code": "POSTMAN10"},
        tests=[status(201), """
const body = pm.response.json();
pm.test("Pendiente", () => pm.expect(body.status).to.eql("pending"));
pm.test("2 x 50 € - 10% = 90.00", () => {
    pm.expect(body.subtotal).to.eql("100.00");
    pm.expect(body.discount_amount).to.eql("10.00");
    pm.expect(body.total).to.eql("90.00");
});
""" + save("orderId", "body.id")]),
    req("Stock reservado", "GET", "/festivals/{{festivalId}}/ticket-types", tests=[status(200), """
const general = pm.response.json().find(t => t.id == pm.collectionVariables.get("ticketTypeId"));
pm.test("Quedan 8 de 10", () => pm.expect(general.quantity_available).to.eql(8));
"""]),
    req("Superar max_per_order → 409", "POST", "/orders", token="token_customer",
        body={"festival_id": "{{festivalId}}", "items": [{"ticket_type_id": "{{ticketTypeId}}", "quantity": 5}]},
        tests=[status(409)]),
    req("Pedido sin items → 422", "POST", "/orders", token="token_customer",
        body={"festival_id": "{{festivalId}}", "items": []}, tests=[status(422)]),
    req("Obtener pedido", "GET", "/orders/{{orderId}}", token="token_customer", tests=[status(200)]),
    req("Otro usuario no ve el pedido → 404", "GET", "/orders/{{orderId}}", token="token_newuser",
        tests=["pm.test(\"403 o 404\", () => pm.expect(pm.response.code).to.be.oneOf([403, 404]));"]),
    req("Pago rechazado (tarjeta acabada en 0000) → 402", "POST", "/orders/{{orderId}}/pay", token="token_customer",
        body={"payment_method": "card", "card_number": "4000000000000000"}, tests=[status(402)]),
    req("Pagar pedido", "POST", "/orders/{{orderId}}/pay", token="token_customer",
        body={"payment_method": "card", "card_number": "4111111111111111"}, tests=[status(200), """
const body = pm.response.json();
pm.test("Pagado", () => pm.expect(body.status).to.eql("paid"));
pm.test("Tiene referencia de pago", () => pm.expect(body.payment_reference).to.be.a("string"));
"""]),
    req("Pagar dos veces → 409", "POST", "/orders/{{orderId}}/pay", token="token_customer",
        body={"payment_method": "bizum"}, tests=[status(409)]),
    req("Mis pedidos", "GET", "/orders", token="token_customer", query={"status": "paid"}, tests=[status(200)]),
    req("Crear pedido VIP (para cancelar)", "POST", "/orders", token="token_customer",
        body={"festival_id": "{{festivalId}}", "items": [{"ticket_type_id": "{{ticketTypeVipId}}", "quantity": 1}]},
        tests=[status(201), save("orderToCancelId", "pm.response.json().id")]),
    req("Cancelar pedido pendiente", "POST", "/orders/{{orderToCancelId}}/cancel", token="token_customer",
        tests=[status(200), 'pm.test("Cancelado", () => pm.expect(pm.response.json().status).to.eql("cancelled"));']),
    req("Pedidos del festival (organizador)", "GET", "/festivals/{{festivalId}}/orders", token="token_organizer",
        tests=[status(200), 'pm.test("2 pedidos", () => pm.expect(pm.response.json().total).to.eql(2));']),
])

entradas = folder("09 · Entradas", [
    req("Mis entradas", "GET", "/tickets", token="token_customer", query={"status": "valid", "limit": 100},
        tests=[status(200), """
const mine = pm.response.json().items.filter(t => t.order_id == pm.collectionVariables.get("orderId"));
pm.test("2 entradas emitidas", () => pm.expect(mine).to.have.lengthOf(2));
pm.collectionVariables.set("ticketId", mine[0].id);
pm.collectionVariables.set("ticketCode", mine[0].code);
pm.collectionVariables.set("ticket2Id", mine[1].id);
pm.collectionVariables.set("ticket2Code", mine[1].code);
"""]),
    req("Obtener entrada", "GET", "/tickets/{{ticketId}}", token="token_customer", tests=[status(200)]),
    req("Nominar entrada", "PATCH", "/tickets/{{ticketId}}", token="token_customer",
        body={"attendee_name": "María López"}, tests=[status(200), """
pm.test("Nominada", () => pm.expect(pm.response.json().attendee_name).to.eql("María López"));
"""]),
    req("Transferir a uno mismo → 400", "POST", "/tickets/{{ticket2Id}}/transfer", token="token_customer",
        body={"email": "customer@example.com"}, tests=[status(400)]),
    req("Transferir a email inexistente → 404", "POST", "/tickets/{{ticket2Id}}/transfer", token="token_customer",
        body={"email": "noexiste{{runId}}@example.com"}, tests=[status(404)]),
    req("Transferir entrada", "POST", "/tickets/{{ticket2Id}}/transfer", token="token_customer",
        body={"email": "{{newUserEmail}}", "attendee_name": "Amigo Invitado"}, tests=[status(200), """
const body = pm.response.json();
pm.test("El código se regenera", () => pm.expect(body.code).to.not.eql(pm.collectionVariables.get("ticket2Code")));
pm.test("Cambia de dueño", () => pm.expect(body.owner_id).to.eql(Number(pm.collectionVariables.get("newUserId"))));
pm.collectionVariables.set("oldTicket2Code", pm.collectionVariables.get("ticket2Code"));
pm.collectionVariables.set("ticket2Code", body.code);
"""]),
    req("El destinatario ve la entrada", "GET", "/tickets/{{ticket2Id}}", token="token_newuser", tests=[status(200)]),
])

puerta = folder("10 · Control de acceso (puerta)", [
    req("Verificar entrada (sin marcarla)", "GET", "/checkin/{{ticketCode}}", token="token_staff",
        query={"festival_id": "{{festivalId}}"}, tests=[status(200), """
const body = pm.response.json();
pm.test("Aceptada", () => { pm.expect(body.accepted).to.be.true; pm.expect(body.reason).to.eql("ok"); });
"""]),
    req("Check-in", "POST", "/checkin", token="token_staff",
        body={"code": "{{ticketCode}}", "festival_id": "{{festivalId}}"}, tests=[status(200), """
const body = pm.response.json();
pm.test("Acceso permitido", () => pm.expect(body.accepted).to.be.true);
pm.test("Marcada como usada", () => pm.expect(body.ticket.status).to.eql("used"));
"""]),
    req("Check-in repetido → already_used", "POST", "/checkin", token="token_staff",
        body={"code": "{{ticketCode}}"}, tests=[status(200), """
const body = pm.response.json();
pm.test("Rechazada por ya usada", () => { pm.expect(body.accepted).to.be.false; pm.expect(body.reason).to.eql("already_used"); });
"""]),
    req("Código antiguo tras transferencia → not_found", "POST", "/checkin", token="token_staff",
        body={"code": "{{oldTicket2Code}}"}, tests=[status(200), """
pm.test("not_found", () => pm.expect(pm.response.json().reason).to.eql("not_found"));
"""]),
    req("Festival equivocado → wrong_festival", "GET", "/checkin/{{ticket2Code}}", token="token_staff",
        query={"festival_id": "999999"}, tests=[status(200), """
pm.test("wrong_festival", () => pm.expect(pm.response.json().reason).to.eql("wrong_festival"));
"""]),
    req("Customer no puede validar → 403", "POST", "/checkin", token="token_customer",
        body={"code": "{{ticket2Code}}"}, tests=[status(403)]),
    req("Nominar entrada usada → 409", "PATCH", "/tickets/{{ticketId}}", token="token_customer",
        body={"attendee_name": "Otro Nombre"},
        tests=["pm.test(\"Rechazado (4xx)\", () => pm.expect(pm.response.code).to.be.within(400, 499));"]),
])

stats = folder("11 · Estadísticas", [
    req("Estadísticas del festival", "GET", "/festivals/{{festivalId}}/stats", token="token_organizer",
        tests=[status(200), """
const body = pm.response.json();
pm.test("Recaudación 90.00", () => pm.expect(body.revenue).to.eql("90.00"));
pm.test("2 emitidas, 1 validada", () => {
    pm.expect(body.tickets_issued).to.eql(2);
    pm.expect(body.tickets_checked_in).to.eql(1);
});
"""]),
    req("Customer no ve estadísticas → 403", "GET", "/festivals/{{festivalId}}/stats", token="token_customer",
        tests=[status(403)]),
])

cierre = folder("12 · Cancelaciones y limpieza", [
    req("Reembolso con entrada usada → 409", "POST", "/orders/{{orderId}}/cancel", token="token_customer",
        tests=[status(409)]),
    req("Quitar actuación del cartel", "DELETE", "/festivals/{{festivalId}}/lineup/{{performanceId}}",
        token="token_organizer", tests=[status(204)]),
    req("Borrar festival publicado → 409", "DELETE", "/festivals/{{festivalId}}", token="token_organizer",
        tests=[status(409)]),
    req("Cancelar festival", "POST", "/festivals/{{festivalId}}/cancel", token="token_organizer", tests=[status(200), """
pm.test("Cancelado", () => pm.expect(pm.response.json().status).to.eql("cancelled"));
"""]),
    req("El pedido pagado queda reembolsado", "GET", "/orders/{{orderId}}", token="token_customer", tests=[status(200), """
pm.test("refunded", () => pm.expect(pm.response.json().status).to.eql("refunded"));
"""]),
    req("Borrar recinto con festivales → 409", "DELETE", "/venues/{{venueId}}", token="token_admin",
        tests=[status(409)]),
    req("Borrar artista", "DELETE", "/artists/{{artistId}}", token="token_admin",
        tests=["pm.test(\"204\", () => pm.expect(pm.response.code).to.eql(204));"]),
    req("Borrar tipo de entrada vendido → 409", "DELETE", "/ticket-types/{{ticketTypeId}}", token="token_organizer",
        tests=["pm.test(\"Rechazado (4xx)\", () => pm.expect(pm.response.code).to.be.within(400, 499));"]),
])

variables = [
    "runId", "token_admin", "token_organizer", "token_staff", "token_customer", "token_newuser",
    "newUserId", "newUserEmail", "venueId", "artistId", "festivalId", "festivalSlug", "ticketTypeId",
    "ticketTypeVipId", "performanceId", "discountId", "orderId", "orderToCancelId", "ticketId", "ticketCode",
    "ticket2Id", "ticket2Code", "oldTicket2Code",
]

collection = {
    "info": {
        "_postman_id": str(uuid.uuid5(uuid.NAMESPACE_URL, "festival-api-postman")),
        "name": "Festival Tickets API · Campo de Gibraltar",
        "description": (
            "Pruebas de la API de venta de entradas de festivales.\n\n"
            "**Antes de ejecutar:**\n"
            "1. `python seed.py --reset` (crea los usuarios de ejemplo con contraseña `Password123`)\n"
            "2. `uvicorn app.main:app --reload`\n"
            "3. Selecciona el entorno *Festival API · Local* y lanza la colección con el **Runner** "
            "en orden (cada petición guarda los ids que usan las siguientes).\n\n"
            "Se puede ejecutar varias veces seguidas: los datos creados llevan un sufijo único (`runId`)."
        ),
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    },
    "auth": {"type": "noauth"},
    "item": [sistema, auth, usuarios, recintos, artistas, festivales, cartel, descuentos, pedidos, entradas,
             puerta, stats, cierre],
    "variable": [{"key": k, "value": ""} for k in variables],
}

environment = {
    "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "festival-api-postman-env")),
    "name": "Festival API · Local",
    "values": [
        {"key": "baseUrl", "value": "http://localhost:8000", "type": "default", "enabled": True},
        {"key": "password", "value": "Password123", "type": "secret", "enabled": True},
    ],
    "_postman_variable_scope": "environment",
}

(OUT / "festival-api.postman_collection.json").write_text(json.dumps(collection, indent=2, ensure_ascii=False) + "\n")
(OUT / "festival-api.local.postman_environment.json").write_text(json.dumps(environment, indent=2, ensure_ascii=False) + "\n")
print("Colección y entorno generados en", OUT)
