# Phase 4 curl verification

October 2, 2026. Requested follow-up using real `curl`, not only Django's test client.

## Current development configuration

A temporary server on port 8001 used the existing environment, with lead alerts explicitly disabled
for that process. Four requests used clearly labeled dummy data and `example.test` email addresses:

| Request | HTTP result | Database outcome |
|---|---|---|
| Lead with valid field structure and dummy token | 503 verification unavailable | No row |
| Lead with invalid email | 400 validation error | No row |
| Newsletter with valid structure and dummy token | 503 verification unavailable | No row |
| Lead with filled honeypot | 201 generic receipt | No row, intentionally |

The actual local **Turnstile secret is still unset**. Valid submissions cannot create records until
it is configured and a valid widget token is supplied. The 503 response is the intended fail-closed
behavior, not a database failure. These checks did not modify any existing records or send email.
They consume the ordinary local per-IP quota; repeated manual requests may therefore return 429
until the window resets. No rate-limit counters were cleared to evade that protection.

Example request used (a placeholder token cannot pass real verification):

```bash
curl --silent --show-error --include \
  --header 'Content-Type: application/json' \
  --header 'Accept: application/json' \
  --data '{"full_name":"CURL TEST - not a customer","email":"curl-check@example.test","message":"CURL TEST - endpoint verification only","locale":"ar","source_path":"/ar/contact","turnstile_token":"not-a-real-token","website":""}' \
  http://127.0.0.1:8001/api/v1/crm/leads/
```

## Successful inserts and negative cases over HTTP

`backend/tests/test_capture_curl.py` starts a real Django test HTTP server and invokes the system
`curl` binary. Requests traverse the normal parsing, validation, Turnstile validation logic,
throttling, database transaction and after-commit email path. Only Cloudflare's external HTTP
response is simulated, inside the isolated test process. Email uses an in-memory outbox. No
production bypass or environment change was added.

Six integration tests passed, covering 19 curl requests. The full backend suite also passed
(**171 tests**), with Ruff and diff checks clean:

| Scenario | Expected and observed |
|---|---|
| JSON lead with Arabic message and attribution | 201; row persisted accurately; alert sent to test outbox after commit |
| URL-encoded lead form | 201; row persisted |
| Newsletter form and repeated mixed-case email | 202 both times; one unconfirmed subscriber |
| Malformed JSON or invalid email | 400; no row |
| Injected internal notes/status, JSON and form | 400; no row |
| Filled honeypot | 201; no row, no provider request or email |
| Rejected/spent token | 400; no row |
| Missing provider configuration | 503; no row |
| Sixth lead request in the same IP window | 429 with Retry-After; exactly five rows |
| GET on either private CRM endpoint | 405; no data exposed |

All capture responses used `Cache-Control: no-store`. The successful responses contained only a
generic receipt, never private data or a record ID. The disposable test database was removed after
the run; no fixture customers/subscribers were left in the development database. Temporary servers
were stopped. No application defect was found in these cases.

To repeat:

```bash
cd backend
source .venv/bin/activate
python manage.py test tests.test_capture_curl --noinput
```

Requires the installed `curl` executable and local PostgreSQL test-database access. Tests are
skipped explicitly if curl is unavailable. Real widget/domain verification remains unverified until
a real Turnstile key and frontend widget are configured; successful fixture tests do not certify it.
