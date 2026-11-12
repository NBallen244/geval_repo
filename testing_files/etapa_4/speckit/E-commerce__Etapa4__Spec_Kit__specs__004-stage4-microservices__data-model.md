# Data Model Specification: Stage 4 Microservices Migration

To ensure complete state separation and service autonomy, each of the three microservices owns a dedicated SQLite database. Sharing of databases, direct cross-service queries, or shared in-memory dictionary singletons is strictly prohibited.

---

## 1. Identity Service Database (`identity.db`)

Manages user registrations, credentials, and roles.

### `users` Table
Stores user accounts. Passwords must be hashed using bcrypt or a secure pbkdf2 algorithm before saving.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `identifier` | TEXT | PRIMARY KEY | Unique user username/identity |
| `password_hash` | TEXT | NOT NULL | Securely hashed password |
| `role` | TEXT | NOT NULL | Either `'customer'` or `'moderator'` |

---

## 2. Commerce Service Database (`commerce.db`)

Manages the product catalog, simulated checkout logs, and the local read projection of approved product reviews.

### `products` Table
Stores the product catalog. This is seeded from `catalog.json` upon service initialization.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `product_id` | TEXT | PRIMARY KEY | Unique product ID (e.g. `'keyboard'`) |
| `name` | TEXT | NOT NULL | Product display name |
| `representative_image` | TEXT | NOT NULL | Public URL or path to image |
| `short_description` | TEXT | NOT NULL | Short product summary |
| `price` | REAL | NOT NULL | Price of the product |
| `general_availability` | TEXT | NOT NULL | `'Yes'` or `'No'` availability |

### `product_reviews` (Event Projection Table)
A read-only local projection of reviews that have been approved. **Only populated by consuming RabbitMQ review events.**

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `review_id` | TEXT | PRIMARY KEY | Unique review ID |
| `product_id` | TEXT | NOT NULL, FK | Refers to product |
| `user_id` | TEXT | NOT NULL | Submitting user ID |
| `rating` | INTEGER | NOT NULL | Rating from 1 to 5 |
| `comment` | TEXT | NOT NULL | User review comment |
| `image_base64` | TEXT | NULL | Base64 encoded image string |
| `created_at` | TEXT | NOT NULL | Timestamp of review creation |

### `processed_events` (Idempotency Table)
Ensures that RabbitMQ message consumption is idempotent. Tracks already-processed event IDs to avoid duplicate handling.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `event_id` | TEXT | PRIMARY KEY | Unique event UUID from incoming message |
| `processed_at` | TEXT | NOT NULL | ISO-8601 timestamp of processing |

### `orders` Table
Stores records of simulated orders processed during checkout.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `order_id` | TEXT | PRIMARY KEY | Unique checkout order UUID |
| `user_id` | TEXT | NOT NULL | Customer username |
| `items_json` | TEXT | NOT NULL | JSON string listing product IDs and quantities |
| `accumulated_total` | REAL | NOT NULL | Final total price |
| `demonstration_info_json` | TEXT | NOT NULL | JSON string with shipping/academic details |
| `created_at` | TEXT | NOT NULL | Checkout timestamp |

---

## 3. Reviews Service Database (`reviews.db`)

Manages submitted product reviews, image attachments, moderation queue state, and the Transactional Outbox.

### `reviews` Table
Stores all submitted reviews along with their moderation status.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `review_id` | TEXT | PRIMARY KEY | Unique review UUID |
| `product_id` | TEXT | NOT NULL | Targeted product ID |
| `user_id` | TEXT | NOT NULL | ID of customer submitting the review |
| `rating` | INTEGER | NOT NULL | Integer rating (1 to 5) |
| `comment` | TEXT | NOT NULL | Textual review |
| `image_base64` | TEXT | NULL | Attached base64 image data |
| `status` | TEXT | NOT NULL | `'pending'`, `'approved'`, or `'rejected'` |
| `created_at` | TEXT | NOT NULL | Submission timestamp |

### `outbox` Table
Stores outbound integration events. Written in the **same database transaction** as updates to the `reviews` table.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `event_id` | TEXT | PRIMARY KEY | Unique event UUID |
| `event_type` | TEXT | NOT NULL | Type of event (e.g. `'review_moderated'`) |
| `payload_json` | TEXT | NOT NULL | JSON string representation of the event payload |
| `status` | TEXT | NOT NULL | `'PENDING'` or `'SENT'` status of publishing |
| `created_at` | TEXT | NOT NULL | Generation timestamp |
