# API & Event Contracts — E-Commerce Stage 4

All JSON uses camelCase on the wire (pydantic alias generator), identical to Stage 3.

## 1. HTTP API (exposed by the gateway; bodies preserved from Stage 3)

### Catalog (→ commerce)
- `GET /products` → 200 `[{ id, name, imageUrl, description, price, available }]`. Cacheable: `X-Cache: HIT|MISS`, `Cache-Control: public, max-age=<ttl>`.
- `GET /products/{id}` → 200 `{ id, name, imageUrl, description, price, available }`; 404 `{ error:"product_not_found", message, productId }`.

### Auth (→ identity)
- `POST /auth/register` `{ identifier, password }` → 201 `{ id, identifier }`; 422 `{ error:"validation_error", message, emptyFields[], nonConformingFields[] }`; 409 `{ error:"identifier_taken", message }`.
- `POST /auth/login` `{ identifier, password }` → 200 `{ active:true, customerId, isModerator? }` (browser-visible; the internal `token` is held by the gateway and never returned to the browser). 401 `{ error:<uniform message> }`. Sets httpOnly session cookie.
- `POST /auth/logout` → 200 `{ active:false, customerId:null }`. Clears the cookie.

### Checkout (→ commerce)
- `POST /checkout/confirm` `{ items:[{ productId, quantity }] }` → 200 `{ items:[{ productId, name, unitPrice, quantity, lineTotal }], total, simulated:true }`; 400 `{ detail:{ code, message } }` (codes `empty_cart`, `invalid_quantity`, `unknown_product`).

### Reviews — public read (→ commerce projection), submit (→ reviews)
- `GET /products/{id}/reviews` → 200 `{ reviews:[ReviewResponse], summary:{ count, average }, ownReview:ReviewResponse|null }`. `no-store`. `reviews`/`summary` are approved-only (projection); `ownReview` is the caller's own non-approved review or null.
- `POST /products/{id}/reviews` (session required) `{ rating, text, title?, images:[{ mediaType, dataBase64 }] }` → 201 `ReviewResponse`; 401 `{ error:"authentication_required", message }`; 404 `{ error:"product_not_found", message }`; 422 `{ error:"validation_error", message, offendingFields[] }`; 409 `{ error:"duplicate_review", message }`.
- `GET /reviews/images/{id}` → raw bytes with stored `Content-Type`; 404 `{ detail:{ error:"image_not_found", message } }` (reviews service).

`ReviewResponse = { id, productId, authorIdentity, rating, title?, text, images:[{ id, imageUrl:"/reviews/images/<id>", mediaType }], moderationState:"pending"|"approved"|"rejected" }`.

### Moderation (→ reviews; moderator session required)
- `GET /moderation/reviews` → 200 `[ReviewResponse]` (pending only); 403 `{ error:"moderator_required", message }`. `no-store`.
- `POST /moderation/reviews/{id}/approve` → 200 `ReviewResponse`; 409 `{ error:"review_not_found"|"already_decided", message }`.
- `POST /moderation/reviews/{id}/reject` → 200 `ReviewResponse`; 409 as above.

### Health (each service + gateway)
- `GET /health` → 200 `{ status:"ok" }`.

### Internal (service-to-service, Bearer; not exposed by the gateway)
- identity `GET /internal/verify` (Bearer) → 200 `{ customerId, identifier, isModerator }` | 401.
- reviews `GET /internal/own-review?productId=&author=` (Bearer) → 200 `ReviewResponse|null`.

## 2. Authentication token

Opaque bearer token issued by identity on login: `base64url(payload).base64url(hmacSHA256(payload, STAGE4_TOKEN_SECRET))` where `payload = { customerId, identifier, isModerator, iat }`. Any service verifies the HMAC with the shared secret and reads the claims. The **role is inside the signed token**, so a client cannot forge a moderator role by sending a header. The gateway forwards the token as `Authorization: Bearer <token>`; services ignore any client-supplied role header.

## 3. Event envelope (versioned, A7)

```json
{
  "eventId": "7c1f...uuid",
  "eventType": "stage4.kiro.review.approved",
  "schemaVersion": "1",
  "occurredAt": "2026-11-07T12:34:56.789Z",
  "correlationId": "a2b9...uuid",
  "data": { ...payload... }
}
```

### Event types & payloads
- `stage4.kiro.review.approved` — data = full `ReviewProjectionData`:
  `{ reviewId, productId, authorIdentity, rating, title, text, images:[{ id, imageUrl, mediaType }], moderationState:"approved" }`.
  Commerce **upserts** this into its projection.
- `stage4.kiro.review.rejected` — data = `{ reviewId, productId, moderationState:"rejected" }`.
  Commerce **removes** `reviewId` from its projection if present.

Routing key = `eventType`. Exchange `stage4.kiro.events` (topic, durable). Messages persistent, published with publisher confirms. Consumer queue `stage4.kiro.commerce.projection` (durable, manual ack, DLX → `stage4.kiro.events.dlx` / `stage4.kiro.commerce.projection.dlq`).

## 4. Delivery semantics

At-least-once delivery with an idempotent consumer keyed on `eventId` (`processed_events`). **Exactly-once is not claimed.** The transactional outbox guarantees an accepted moderation change is eventually published even across a broker outage; duplicates are absorbed idempotently.

## 5. Environment variables (defaults from stage4-runtime.json)

`GATEWAY_PORT=18200`, `IDENTITY_PORT=18201`, `COMMERCE_PORT=18202`, `REVIEWS_PORT=18203`, `FRONTEND_PORT=18300`,
`AMQP_URL=amqp://ecommerce:stage4-demo@127.0.0.1:5672/stage4_kiro`, `EVENT_NAMESPACE=stage4.kiro`,
`IDENTITY_URL=http://127.0.0.1:18201`, `COMMERCE_URL=http://127.0.0.1:18202`, `REVIEWS_URL=http://127.0.0.1:18203`,
`STAGE4_TOKEN_SECRET=<demo secret>`, `CATALOG_CACHE_TTL_SECONDS=30`, `CATALOG_CACHE_MAX_ENTRIES=256`,
`<SERVICE>_DB_PATH` for each SQLite file, `REVIEW_IMAGE_DIR` for reviews images.
