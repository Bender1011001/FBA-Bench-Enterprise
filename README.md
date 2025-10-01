# FBA-Bench Enterprise (Staging)

## Login UI (Manual Test)

### Setup
- Copy [repos/fba-bench-enterprise/web/.env.example](repos/fba-bench-enterprise/web/.env.example) to `web/.env` and set `VITE_API_BASE_URL` to your backend URL (default: `http://localhost:8000`).

### Run Dev Server
From the web directory:
```bash
cd repos/fba-bench-enterprise/web
npm i
npm run dev
```
Opens at http://localhost:5173.

### Manual Test Path
1. Start the backend API (e.g., `uvicorn api.server:app --reload` from enterprise root).
2. Register a user via API (e.g., using curl or Postman: POST /auth/register with email/password) or use a pre-existing user.
3. Visit http://localhost:5173, enter credentials in the Login form, and submit.
4. On success: See "Signed in" message; token stored in localStorage by the frontend client (key: `fbaee_access_token`).
5. Test errors: Invalid credentials (401: "Invalid email or password"), invalid input (400: "Invalid input"), network issues ("Something went wrong").

Notes: Tokens persist in localStorage; no auto-login implemented here. Client-side validation blocks empty/invalid email or empty password.

This is the staging directory for the private enterprise distribution of FBA-Bench created during Phase 1 (local bifurcation).
Do not push directly from here; remote setup and CI will be prepared in later steps.

Contents (to be added in subsequent steps):
- Backend/API app, services, infra, and proprietary scenarios/red-team content
- Packaging/requirements configured to depend on the core via editable local path
- CI ([.github/workflows/ci.yml](.github/workflows/ci.yml)) tailored for enterprise integration tests

## Running the API Locally

1. Copy `.env.example` to `.env` in the `repos/fba-bench-enterprise` directory and edit as needed (e.g., set `DATABASE_URL` for Postgres if desired).

2. Install dependencies:
   - With Poetry: `poetry install` (from the workspace root, assuming Poetry is configured for the enterprise repo).
   - Or with pip: `pip install -r repos/fba-bench-enterprise/requirements.txt`

3. Apply database migrations (from workspace root):
   - With Poetry: `poetry run alembic -c repos/fba-bench-enterprise/alembic.ini upgrade head`

## Frontend API Client (Auth)

The frontend auth client is a lightweight, framework-agnostic TypeScript library for authentication with the Enterprise API. It provides methods for `register`, `login` (with automatic token storage), and `me` (fetch current user). Includes HTTP utilities, token persistence, and typed error handling.

### Location and Setup

Client files: `repos/fba-bench-enterprise/frontend/src/api/`
- HTTP wrapper: [`http.ts`](repos/fba-bench-enterprise/frontend/src/api/http.ts)
- Token storage: [`tokenStorage.ts`](repos/fba-bench-enterprise/frontend/src/api/tokenStorage.ts)
- Auth methods: [`authClient.ts`](repos/fba-bench-enterprise/frontend/src/api/authClient.ts)
- Tests: [`__tests__/authClient.test.ts`](repos/fba-bench-enterprise/frontend/src/api/__tests__/authClient.test.ts)

Install and build:
```bash
cd repos/fba-bench-enterprise/frontend
npm install
npm run build  # tsc
npm run test   # vitest
```

Compiles to `dist/` with types.

### Configuration

- **VITE_API_BASE_URL**: Backend base URL (Vite env var).
  - Set in `.env` (e.g., `VITE_API_BASE_URL=https://api.example.com`).
  - Fallback: `http://localhost:8000`.
  - Override via `opts.baseUrl` in `createAuthClient()`.

Copy [`frontend/.env.example`](repos/fba-bench-enterprise/frontend/.env.example) to `.env` and update for your environment (dev/staging/prod).

### Token Storage

Uses pluggable storage (default: localStorage with key `fbaee_access_token` for scoping).
- **Persistence**: localStorage (browser) with in-memory cache for efficiency.
- **Fallback**: In-memory only (non-browser/SSR).
- **Helpers**:
  - `isAuthenticated()`: Returns `true` if token exists.
  - `getAuthHeader()`: Returns `{ Authorization: 'Bearer <token>' }` or `{}`.
- **Clear on logout**: Call `storage.clearToken()` to remove token.
- **Caution**: localStorage exposes tokens to XSS; use CSP/HTTPS in prod. For SSR, use in-memory or server-side storage. No refresh tokens in this client.

Custom storage: Pass via `opts.storage` in `createAuthClient()`.

### Usage Example

```typescript
import { createAuthClient } from './src/api/authClient'; // Adjust path

// Init (VITE_API_BASE_URL from env)
const client = createAuthClient();

// Register (normalizes email: trim + lowercase)
try {
  const user = await client.register(' User@Example.com ', 'SecurePass123!');
  console.log(user); // { id, email, is_active, subscription_status, created_at, updated_at }
} catch (error) {
  if ('status' in error && error.status === 400) {
    console.error('Validation error:', error.message); // e.g., password too short
  } else if (error.status === 409) {
    console.error('Email already registered');
  }
}

// Login (stores token automatically)
try {
  const tokens = await client.login('user@example.com', 'SecurePass123!');
  console.log(tokens); // { access_token, token_type: 'bearer', expires_in: 900 }
  // Token stored; subsequent calls auto-attach header
} catch (error) {
  if (error.status === 401) {
    console.error('Auth error:', error.reason); // 'invalid_credentials' or 'unauthorized'
  }
}

// Fetch profile (requires token; clears on 401)
try {
  const me = await client.me();
  console.log(me); // UserPublic
} catch (error) {
  if (error.status === 401) {
    // Redirect to login
    console.error('Unauthorized; session expired');
  }
}

// Manual logout
const storage = createTokenStorage();
storage.clearToken(); // Clears localStorage and cache
```

### Error Handling

- **ValidationError (400)**: Invalid input (e.g., weak password); `error.message` has details.
- **AuthError (401)**: Login fail or unauthorized; `error.reason` specifies cause.
- **ConflictError (409)**: Duplicate email.
- **ApiError (others)**: Generic with `status` and `message`.

Aligns with backend endpoints: POST /auth/register, POST /auth/login, GET /auth/me.

For full integration, see the [demo UI in web/](repos/fba-bench-enterprise/web/) (uses this client).
- **Default (browser)**: [`LocalStorageTokenStorage`](repos/fba-bench-enterprise/frontend/src/api/tokenStorage.ts) using keys `access_token` and `refresh_token`. Guards against SSR by checking `typeof window !== 'undefined'`.
- **Fallback (non-browser/SSR)**: [`InMemoryTokenStorage`](repos/fba-bench-enterprise/frontend/src/api/tokenStorage.ts) for session-only storage.
- Custom: Pass your own `TokenStorage` implementation via `opts.storage` in `createAuthClient()`.

Tokens are cleared on logout or error. Refresh tokens are stored but not auto-refreshed in this minimal client.

### Usage Examples (TypeScript)

#### Initialization

```typescript
import { createAuthClient } from './src/api/authClient'; // Adjust path as needed

const client = createAuthClient({
  baseUrl: 'http://127.0.0.1:8000',
  // storage: customStorage // Optional
});
```

#### Register

```typescript
try {
  const user = await client.register('user@example.com', 'securepassword123');
  console.log(user); // { id, email, created_at, updated_at, is_active, subscription_status }
} catch (error) {
  if (error.name === 'ArgumentError') {
    console.error(error.detail); // e.g., "Email is required"
  } else if (error.name === 'ConflictError') {
    console.error('User already exists:', error.detail);
  } else if (error.name === 'BadRequestError') {
    console.error('Invalid input:', error.detail);
  }
}
```

#### Login

```typescript
try {
  const tokens = await client.login('user@example.com', 'securepassword123');
  console.log(tokens); // { access_token, token_type: 'bearer' }
  // Tokens automatically stored
} catch (error) {
  if (error.name === 'UnauthorizedError') {
    console.error('Invalid credentials:', error.detail);
  } else if (error.name === 'BadRequestError') {
    console.error('Invalid input:', error.detail);
  }
}
```

#### Me (Current User)

```typescript
try {
  const user = await client.me();
  console.log(user); // Public user profile
} catch (error) {
  if (error.name === 'UnauthorizedError') {
    console.error('Token invalid/missing:', error.detail);
    // Optionally clear storage: storage.clear()
  }
}
```

Client-side validation:
- Email: Non-empty string
- Password: 8–128 characters
Throws `ArgumentError` before network calls.

Error propagation: HTTP errors (400/401/403/409) are thrown as typed objects with `name`, `status`, and `detail`.

### Security Notes

- Tokens are stored in LocalStorage by default (not cookies) to avoid CSRF, but this exposes them to XSS attacks. Implement Content Security Policy (CSP), sanitize inputs, and use HTTPS in production.
- Never commit `.env` files with secrets.
- For SSR (e.g., Next.js), use InMemoryTokenStorage or a server-side strategy.
- Refresh tokens are stored but not used for auto-refresh in this client; implement manually if needed.
- Aligns with backend: See [api/routers/auth.py](repos/fba-bench-enterprise/api/routers/auth.py) for endpoint details (POST /auth/register, POST /auth/login, GET /auth/me).

## Frontend — Login UI (Demo)

A minimal Vite + React TypeScript app demonstrating login with the auth client library. Renders a form, performs client-side validation, calls the API, and displays the user profile on success.

### Prerequisites
- Node.js 18+

### Setup

1. **Build the auth client (from Step 5)**:
   ```bash
   cd repos/fba-bench-enterprise/frontend
   npm i
   npx tsc -p .
   ```
   This creates the `dist/` directory needed for imports.

2. **Install and run the UI**:
   ```bash
   cd repos/fba-bench-enterprise/web
   npm i
   npm run dev
   ```
   Opens at `http://localhost:5173` (default Vite port).

### Configuration
- Edit `window.API_BASE_URL` in [web/index.html](repos/fba-bench-enterprise/web/index.html) to point to your backend (default: `http://127.0.0.1:8000`).

### Manual Testing Flow
- Ensure the backend API is running (e.g., via `uvicorn api.server:app --reload`).
- Register a user via API (POST `/auth/register`) or use an existing account.
- In the UI: Enter credentials, submit → see loading state → profile displays on success (ID, email, dates, active status, subscription).
- Invalid inputs: Inline errors for email/password.
- Server errors: Banner for 400 (bad request), 401 (invalid credentials), 403 (inactive user).

### Notes
- Minimal demo UI for authentication only; no production styling or registration form.
- Uses inline styles; extend with CSS frameworks if needed.
- Optional unit test: `cd web && npm test` (validates client-side form behavior).

## Frontend — Registration UI (Demo)

A minimal extension to the Login UI demonstrating registration. Includes a toggle between Login and Register forms, client-side validation mirroring backend rules, API calls to `/auth/register`, loading states, inline errors, and server error banners (400/409). On success, shows confirmation and prompts to switch to Login (no auto-login).

### Prerequisites
- Node 18+

### Build the auth client (Step 5):
```bash
cd repos/fba-bench-enterprise/frontend && npm i && npx tsc -p .
```

### Run the web app:
```bash
cd repos/fba-bench-enterprise/web && npm i && npm run dev
```

### Configure API base URL:
- Edit `window.API_BASE_URL` in [web/index.html](repos/fba-bench-enterprise/web/index.html)

### Manual flow:
- Switch to Register tab, create a new account; on success, switch to Login and authenticate
- Error scenarios:
  - 409 duplicate email, 400 invalid inputs; check server banner details

### Notes
- Toggle between forms via buttons (no routing).
- Client validation: Email (non-empty, contains @); Password (8-128 chars, lowercase/uppercase/digit/special).
- Server errors: 409 → "Email already registered"; 400 → "Invalid input".
- Success: Clears form, shows message to proceed to Login.
- Unit test: `cd web && npm run test` (validates pre-submit behavior in RegisterForm.test.tsx).

## Auth — Registration

### Endpoint
**POST** `/auth/register`

### Request
JSON body with:
- `email`: Valid email address (validated via Pydantic `EmailStr`; requires `email-validator` dependency)
- `password`: String (8–128 characters, at least 1 lowercase, 1 uppercase, 1 digit, 1 non-alphanumeric symbol)

Example:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

### Response
- **201 Created**: Safe user fields (no password or hash)
```json
{
  "id": "uuid-string",
  "email": "user@example.com",
  "is_active": true,
  "subscription_status": null,
  "created_at": "2023-01-01T00:00:00",
  "updated_at": "2023-01-01T00:00:00"
}
```

### Errors
- **400 Bad Request**: Invalid email format or password policy violation (e.g., too short, missing character class)
  - Detail: Specific message like "Password must contain at least one digit"
- **409 Conflict**: Duplicate email (case-insensitive; email is normalized to lowercase)
  - Detail: "Email already registered"

### Password Policy
- Length: 8–128 characters
- At least one lowercase letter (`a-z`)
- At least one uppercase letter (`A-Z`)
- At least one digit (`0-9`)
- At least one symbol (any non-alphanumeric character)

### Notes
- Email is normalized: converted to lowercase and trimmed before storage/checks.
- Passwords are securely hashed with Argon2id (parameters configurable via environment variables; see `api/security/passwords.py` and `.env.example`).
- Unique constraint enforced at DB level; IntegrityError mapped to 409.
- No JWT tokens issued on registration (use `/auth/login` for authentication).
- Tests: `pytest repos/fba-bench-enterprise/tests/test_auth_register.py -q`

## Auth — Login

### Endpoint
**POST** `/auth/login`

### Request
JSON body with:
- `email`: string (will be normalized: trimmed and lowercased)
- `password`: string

Example:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

### Response
- **200 OK**: JWT access token and metadata
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### Errors
- **401 Unauthorized**: `{"detail": "Invalid credentials"}` (unknown email or wrong password)
- **401 Unauthorized**: `{"detail": "Inactive account"}` (user exists but is inactive)

### Notes
- Email lookup is case-insensitive due to normalization.
- Password verification uses Argon2id (see `api/security/passwords.py`).
- JWT access tokens are short-lived (default 15 minutes; configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`).
- Claims include `sub` (user ID), `email`, `token_type: "access"`, `iat`, `exp`.
- No refresh token in this implementation (add later if needed).
- For protected routes, use `Authorization: Bearer <access_token>`.
- JWT config via environment variables; see `.env.example` for defaults (use secure secrets in production).
- Tests: `pytest repos/fba-bench-enterprise/tests/test_auth_login.py -q`

## Auth — Profile

### Endpoint
**GET** `/auth/me`

### Auth
Bearer token from `/auth/login` in `Authorization: Bearer <access_token>` header.

### Response
- **200 OK**: Safe user profile fields
```json
{
  "id": "uuid-string",
  "email": "user@example.com",
  "is_active": true,
  "subscription_status": null,
  "created_at": "2023-01-01T00:00:00",
  "updated_at": "2023-01-01T00:00:00"
}
```

### Errors
- **401 Unauthorized**: `{"detail": "..."}` with `WWW-Authenticate: Bearer` header when missing/invalid/expired token or inactive user.
  - Missing Authorization header
  - Invalid or expired JWT
  - User not found or inactive (`"inactive_user"`)

### Notes
- Returns `UserPublic` schema excluding password or `password_hash`.
- Protected by `get_current_user` dependency (JWT validation + active user check).
- Email is normalized (lowercase) as per registration/login.
- JWT configuration and expiry per environment variables (see `.env.example` and `DEV_SETUP.md`).
- Tests: `pytest repos/fba-bench-enterprise/tests/test_auth_me.py -q`

## Frontend — Account Page

The Account page extends the authentication UI with a dedicated view for authenticated users. It displays the public user profile fetched from the `/auth/me` endpoint and provides a Sign Out control that clears stored tokens and returns to the login view.

### Features
- **Profile Display**: Shows user details including ID, email, creation/update dates, active status, and subscription status.
- **Sign Out**: Removes `access_token` and `refresh_token` from localStorage, clears in-memory user state, and navigates back to the login view.
- **Guarded Access**:
  - On app load, if tokens exist in storage, automatically fetches the profile. Success shows the Account view; failure (e.g., expired token) clears tokens and shows login with an error.
  - Unauthenticated users clicking "Account" are redirected to login with a non-blocking notice: "Please sign in to view your account."
- **Navigation**: Simple tab buttons for Login, Register, and Account (no router library).

### Prerequisites and Setup
- Build the auth client first (Step 5):
  ```bash
  cd repos/fba-bench-enterprise/frontend && npm i && npx tsc -p .
  ```
- Run the web app:
  ```bash
  cd repos/fba-bench-enterprise/web && npm i && npm run dev
  ```
- Ensure the backend API is running (e.g., `uvicorn api.server:app --reload` from the enterprise root).

### Manual Workflow
1. Load the app without tokens: Lands on login view.
2. Register a new user (via Register tab), then switch to Login and authenticate: Switches to Account view showing profile.
3. In Account view, click Sign Out: Clears tokens, returns to login.
4. Test invalid token: Manually set an invalid `access_token` in browser dev tools localStorage, reload: App clears tokens and shows login with "Session expired" error.
5. Attempt Account tab without login: Shows login with notice to sign in.

### Notes
- Leverages the existing auth client for profile fetch and token handling.
- Inline styles consistent with prior UI; no new dependencies.
- Optional unit test: `cd web && npm run test` (verifies Sign Out button clears storage and invokes callback via localStorage spies in JSDOM).
- For production, consider adding token refresh logic or secure storage alternatives.

## Billing — Checkout Session

### Endpoint
POST /billing/checkout-session (auth required)

### Request JSON example:
- {}
- {"price_id": "price_ABC", "quantity": 2}

### Response example:
{"url": "https://checkout.stripe.com/c/session/abc..."}

### Configuration: STRIPE_SECRET_KEY, STRIPE_PRICE_ID_DEFAULT, FRONTEND_BASE_URL.

### Notes
Returns a URL to redirect the user; do not expose secret keys; see Step 10 for webhooks.

## Stripe Billing — Webhooks

### Endpoint

`POST /billing/webhook`

This endpoint handles incoming Stripe webhook events to update user subscription status in the database. It is unauthenticated and relies on Stripe signature verification for security. Requires the `Stripe-Signature` header.

### Supported Events and Status Mappings

The endpoint processes the following events and maps Stripe statuses to the `users.subscription_status` field:

| Event Type                  | Action / Mapping                                                                 |
|-----------------------------|----------------------------------------------------------------------------------|
| `checkout.session.completed` | Sets `"active"` (if subscription mode and paid). Resolves user via `metadata.user_id`, `client_reference_id`, or email (`customer_details.email` or `customer_email`). |
| `customer.subscription.updated` | Maps status: `active` or `trialing` → `"active"`; `past_due` or `unpaid` → `"past_due"`; `canceled` or `incomplete_expired` → `"canceled"`. Resolves via `metadata.user_id` or `customer_email` (if present). |
| `customer.subscription.deleted` | Sets `"canceled"`. Resolves via `metadata.user_id` or `customer_email` (if present). |
| `invoice.payment_succeeded` | Ensures `"active"` (if user resolved). Resolves via `customer_email`.             |
| `invoice.payment_failed`    | Sets `"past_due"`. Resolves via `customer_email`.                                |

- Unknown/unsupported events: Ignored (200 OK).
- User not resolved: Acknowledged (200 OK, no DB change).
- Updates are idempotent: Only changes status if different; safe for retries.

### Responses

- **200 OK**: `{"received": true}` (processed or ignored event).
- **400 Bad Request**: `{"detail": "Invalid signature"}` (verification failure).
- **503 Service Unavailable**: `{"detail": "Billing unavailable"}` (missing `STRIPE_WEBHOOK_SECRET`).

### Configuration

- `STRIPE_WEBHOOK_SECRET`: Webhook signing secret (e.g., `whsec_...`). Set in `.env`; obtain from Stripe Dashboard > Developers > Webhooks. Never commit real secrets; configure per-environment securely. Missing secret returns 503.

### Testing

- Run: `pytest repos/fba-bench-enterprise/tests/test_billing_webhooks.py -q`
- Tests patch `stripe.Webhook.construct_event` (no network calls); cover verification errors, all events/mappings, user resolution (ID/email/client_ref), idempotency, and ignores (no user/unknown event).

### Local Testing (Optional)

Use Stripe CLI to forward events locally:

```bash
stripe listen --forward-to http://localhost:8000/billing/webhook --events checkout.session.completed,customer.subscription.updated,customer.subscription.deleted,invoice.payment_succeeded,invoice.payment_failed
```

Note: Idempotent; events without resolvable user acknowledged (200) without change. No extra Stripe API calls in handler.

## Billing — Customer Portal

### Endpoint

`POST /billing/portal-session` (auth required)

### Behavior

Looks up Stripe customer by email; returns portal URL; 404 if none found.

### Request

Empty JSON: `{}`

### Response

- **200 OK**: `{"url":"https://billing.stripe.com/p/session/..."}`

- **401 Unauthorized**: `{"detail": "Could not validate credentials"}` (via JWT dependency).

- **503 Service Unavailable**: `{"detail": "Billing unavailable"}` (missing `STRIPE_SECRET_KEY`).

- **404 Not Found**: `{"detail": "No Stripe customer found"}` (user likely hasn’t subscribed yet).

- **500 Internal Server Error**: `{"detail": "Failed to create portal session"}` (Stripe exceptions; sanitized).

### Configuration

- `STRIPE_SECRET_KEY`: Required (e.g., `sk_test_...`).

- `FRONTEND_BASE_URL`: For default return URL (e.g., `http://localhost:5173`).

- `STRIPE_PORTAL_RETURN_URL`: Optional override for return URL; defaults to `FRONTEND_BASE_URL + "/account"`.

### Example Usage (curl)

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Password123!"}' | jq -r '.access_token')

curl -X POST http://127.0.0.1:8000/billing/portal-session \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

Response:
```json
{"url":"https://billing.stripe.com/p/session/..."}
```

### Billing Page

The web frontend Billing page includes:

- **Subscribe**: Calls `/billing/checkout-session` to get URL and navigates (existing).

- **Manage Billing**: Calls `/billing/portal-session` to get URL and navigates; shows "No billing account found. Please subscribe first." on 404; "Billing is currently unavailable." on errors.

Buttons disable during requests with "Loading..." text and `aria-busy` for accessibility.

### Testing

- Backend: `pytest repos/fba-bench-enterprise/tests/test_billing_portal.py -q` (mocks Stripe; covers auth, config, customer lookup, success, errors).

- Frontend: Basic tests in `web/src/components/BillingPage.test.tsx` (button clicks, loading, 404 handling).

## Account Page (Manual Test)

### Prereq
- Set `VITE_API_BASE_URL` (see [web/.env.example](repos/fba-bench-enterprise/web/.env.example)) and run backend.

### Steps
- From web/: `npm i && npm run dev`
- If not logged in, you’ll see Login (use Register then Login as needed).
- After login, Account page shows your profile (email, subscription status, timestamps).
- Use “Sign out” to clear session and return to Login.

### Notes
- Unauthenticated or expired tokens will redirect you to Login.
- Profile data is fetched client-side from `/auth/me` via the shared auth client.

## CI and Coverage

The GitHub Actions CI workflow at [.github/workflows/ci.yml](.github/workflows/ci.yml) runs on push and pull requests to any branch:

- Backend: Python 3.10/3.11 matrix with pytest and coverage on the API code (`--cov=api`), producing `coverage.xml` (terminal report + XML for artifacts) and uploading as artifact.
- Frontend: Node 18.x unit tests (Vitest) for both `frontend/` (auth client) and `web/` packages, plus build checks (TypeScript compilation/Vite build; skips if no script).

Stripe and webhook calls are fully mocked in tests; no real network or API keys required. Coverage focuses on critical paths (auth, billing endpoints).

Local CI parity: See [DEV_SETUP.md](DEV_SETUP.md) for commands matching the workflow.
