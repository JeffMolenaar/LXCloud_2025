API Reference — LXCloud
======================

Dit document somt de HTTP API endpoints op die in de applicatie beschikbaar zijn (voor gebruik met Postman of curl). Deze API's bevinden zich hoofdzakelijk onder de `/api` blueprint en een aantal JSON endpoints onder admin/controllers.

Authenticatie

De API gebruikt `Flask-Login` voor authenticatie; endpoints die `@login_required` hebben vereisen een ingelogde sessie (cookie) of een andere sessie-authenticatie.

Voor testen met Postman: eerst POST naar `/auth/login` (form fields `username` + `password`) en bewaar de cookie in Postman (Enable "Automatically follow redirects" en "Store cookies").

Algemene headers

`Content-Type: application/json` voor JSON body requests

`Accept: application/json` wordt aanbevolen

Endpoints (samenvatting + voorbeelden)
-------------------------------------

Base URL: `http://<server>` (op productie: server IP of domein)

`GET /api/controllers/status`

Beschrijving: Haal realtime status op van controllers (admin ziet alle controllers, normale gebruikers alleen die van zichzelf).

Auth: login required

Params: geen

Response: JSON array met elementen {id, serial_number, name, type, is_online, last_seen}

Curl:

```bash
curl -b cookiejar -c cookiejar -X GET http://localhost/api/controllers/status
```

`GET /api/controllers/<id>/recent-data`

Beschrijving: Haal recente data points van controller (per ID)

Auth: login required

Query params: `hours` (integer, default 24)

Response: JSON array met {timestamp, data}

Curl voorbeeld:

```bash
curl -b cookiejar -c cookiejar "http://localhost/api/controllers/5/recent-data?hours=6"
```

`GET /api/stats/overview`

Beschrijving: Overzicht statistieken (admin krijgt extra velden)

Auth: login required

Response: JSON object met total_controllers, online_controllers, offline_controllers, total_users (admin only), unbound_controllers

`GET /api/system/status`

Beschrijving: Systeemstatus inclusief achtergrondservices (admin only)

Auth: login required (admin)

Response: JSON object met mqtt_service, controller_status_service, version

`GET /api/map-data`

Beschrijving: Map-data voor controllers met locatie

Auth: login required

Response: JSON array met {id, name, serial_number, latitude, longitude, is_online, type, last_seen}

`POST /api/controllers/register`

Beschrijving: Device registration endpoint (controller POSTs JSON to register or update)

Auth: public (controllers authenticate by serial number and registration)

Body (JSON) required example:

```json
{
  "serial_number": "250100.1.0625",
  "type": "speedradar",
  "name": "250100.1.0625",
  "latitude": 51.913071,
  "longitude": 5.713852,
  "timeout_seconds": 300
}
```

- Valid controller types: `speedradar`, `beaufortmeter`, `weatherstation`, `aicamera`.
- Responses: 201 on create, 200 when updating existing controller, 400 for validation errors.
- Curl:

```bash
curl -X POST http://localhost/api/controllers/register \
  -H "Content-Type: application/json" \
  -d '{"serial_number":"250100.1.0625","type":"speedradar"}'
```

`POST /api/controllers/<serial>/data`

Beschrijving: Controller stuurt sensor data

Auth: public

Path param: `serial` (case-insensitive, stored uppercase)

Body: JSON payload with arbitrary data fields; `latitude`/`longitude` are stripped and used to update location if present

Responses: 200 on success, 404 if controller not found

`POST /api/controllers/<serial>/status`

Beschrijving: Update online/offline status

Body: JSON: {"online": true/false}

Responses: 200 success, 404 not found

`PUT /api/controllers/<serial>`

Beschrijving: Wijzig controller configuratie (naam, type, coords, timeout)

Auth: public (but updates require the controller to exist; UI edits require login)

Body: JSON with fields to change (see code: `name`, `type`, `latitude`, `longitude`, `timeout_seconds`)

`GET /api/controllers/<serial>`

Beschrijving: Haal controller info op

Responses: 200 with `controller` object, 404 if not found

`GET /api/controllers/list`

Beschrijving: List controllers voor gebruiker of admin

Auth: login required

Response: {controllers: [...], total: N}

`GET /api/controllers/register` (helper)

Beschrijving: Als iemand per ongeluk GET doet op registration endpoint: return help message, example curl and example body (returns 405)

`GET/POST /api/controllers/debug`

Beschrijving: Debug endpoint die request-headers en eenvoudige diagnose teruggeeft


Admin / Controllers (UI JSON endpoints)

---------------------------------------

GET /controllers/api/all (admin)

  Beschrijving: JSON lijst met alle controllers inclusief owner info

  Auth: login required + admin

GET /admin/api/marker-config

  Beschrijving: JSON met marker configuratie voor dashboard

  Auth: none (public function in code), maar meestal gebruikt door frontend via authenticated requests

Auth & Postman tips

Voor alle `login_required` endpoints: eerst POST login via `/auth/login` (form), sla cookies op in Postman. Voor API-only testing kun je een session-cookie exporteren uit een browser en in Postman plakken.

Alternatief: maak een test admin user via `python database_utils.py create` of `python database_utils.py init` op een lokale dev instance, of gebruik de `admin_credentials` file als die door de installer is aangemaakt.

Voorbeeld Postman-request (Register controller)

---------------------------------------

Method: POST

URL: `http://localhost/api/controllers/register`

Headers: `Content-Type: application/json`

Body (raw JSON):

```json
{
  "serial_number": "250100.1.0625",
  "type": "speedradar",
  "name": "250100.1.0625",
  "latitude": 51.913071,
  "longitude": 5.713852
}
```

 
Notes / Known behaviors
-----------------------
- Registration endpoint normaliseert `serial_number` (uppercase) en `type` (lowercase).
- Reserved serial path words: `register`, `list`, `debug` are protected and return helpful errors if used as serial numbers.
- Many UI endpoints are form-based; prefer the JSON `/api/...` endpoints for Postman testing.

Als je wilt, kan ik deze API-documentatie uitbreiden met een Postman collection JSON export (geformatteerde collection) zodat je die direct kunt importeren in Postman. Wil je dat ik dat genereer, of is `api.md` voorlopig genoeg?
