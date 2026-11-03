# Data Model: Stage 1 E-Commerce Application

This document defines the key data entities and properties for the Stage 1 E-Commerce Application, derived strictly from the functional requirements and represented as technical choices.

## Data Schema & Entities

### 1. Product (Technical Schema)
Represents a product item in the catalog. Product identifiers are treated strictly as internal technical references and are not user-facing requirements.

- **Properties**:
  - `product_id` (String): Internal technical reference identifier.
  - `name` (String): Product name displayed in the catalog.
  - `representative_image` (String): Reference representing the product.
  - `short_description` (String): Short descriptive text.
  - `price` (Decimal): Numeric price value.
  - `general_availability` (String): Display status of general availability.

---

### 2. UserAccount (Technical Schema)
Represents a registered customer account stored in-memory on the backend component. This uses a technology-neutral identifier and password as the minimal authentication contract, without requiring username/email semantics, field lengths, or uniqueness thresholds beyond what is essential to express incomplete or invalid inputs.

- **Properties**:
  - `identifier` (String): Technology-neutral customer identification string.
  - `hashed_password` (String): Password representation. Passwords must not be displayed or stored as readable plain text.

---

### 3. CartItem (Technical Frontend State)
Represents a specific product and quantity added to the local shopping cart, managed in React state.

- **Properties**:
  - `product_id` (String): Internal technical reference to the Product.
  - `name` (String): Consistent name representing the Product.
  - `unit_price` (Decimal): Consistent price representing the Product.
  - `quantity` (Integer): The selected count of that product in the cart.
  - `subtotal` (Decimal): Calculated representation of price and quantity.

---

### 4. LocalCart (Technical Frontend State)
Represents the local shopping cart state managed on the client side in React state.

- **Properties**:
  - `items` (List of CartItem): Currently selected items.
  - `accumulated_total` (Decimal): Accumulated total of selected items.

---

### 5. UserSession (Technical Schema)
Represents an active session generated upon successful authentication.

- **Properties**:
  - `session_token` (String): Unique identifier token generated on successful sign-in, destroyed or invalidated upon sign-out.
  - `identifier` (String): Reference to the associated customer's UserAccount identifier.

---

### 6. SimulatedOrder (Technical Schema)
Represents a successfully confirmed checkout.

- **Properties**:
  - `items` (List of CartItem): Snapshot of cart items.
  - `accumulated_total` (Decimal): Accumulated purchase total at checkout.
  - `demonstration_info` (Dictionary): Opaque and minimal demonstration details entered by the user (no specific customer or contact fields are mandated).
