# Epics and User Stories - Stage 1 E-Commerce Case

This document decomposes the requirements for Stage 1 of the E-Commerce Case into atomic, independent, and verifiable User Stories. Each story contains exact Acceptance Criteria (AC) mapped directly from the canonical seed specification (`especificacion-semilla-final-en.md`) and the approved planning roadmap, correcting all over-prescribed or invented constraints.

---

## Epic 1: Product Catalog

### Story 1.1: Browse Product Catalog
* **As a** visitor
* **I want to** view a catalog of available products
* **So that** I can recognize items, see their details, and make an initial purchase decision.

#### Acceptance Criteria:
* **AC 1.1.1 (No Authentication Required)**: The catalog must be accessible and browsable without requiring any form of user registration or sign-in.
* **AC 1.1.2 (Product Details)**: Each product listed in the catalog must clearly display:
  - Product Name
  - Representative Image
  - Short Description
  - Price
  - General Availability
* **AC 1.1.3 (Data Consistency)**: Product information must remain consistent between the user interface and the rest of the application flow.
* **AC 1.1.4 (Optional Expanded Product View)**: If an expanded product view is included:
  - It must complement the catalog.
  - It must preserve the same commercial information (name, price, image, description, and availability).
* **AC 1.1.5 (Functional Boundaries)**: No quick text search, advanced filters, recommendations, or complex catalog classification are included.

---

## Epic 2: Shopping Cart

### Story 2.1: Add Products to Cart
* **As a** user
* **I want to** add products from the catalog to a shopping cart managed locally by the application
* **So that** I can compile items for a potential purchase.

#### Acceptance Criteria:
* **AC 2.1.1 (Cart Content Display)**: The cart must clearly communicate which products it contains, their quantities, their individual prices, and the accumulated purchase total.
* **AC 2.1.2 (Immediate Visual Feedback)**: Adding an item must provide visible feedback, and changes must be reflected immediately in the interface.
* **AC 2.1.3 (Active Journey Retention)**: Cart contents must remain available throughout the person's active journey.

### Story 2.2: Manage Shopping Cart Content
* **As a** user
* **I want to** adjust quantities and remove items within the shopping cart
* **So that** I can customize my order.

#### Acceptance Criteria:
* **AC 2.2.1 (Quantity Adjustment)**: The cart must allow the person to adjust quantities of individual products in the cart. Adjusting quantities must recalculate product totals and the overall accumulated total, with changes reflected immediately.
* **AC 2.2.2 (Item Removal)**: The cart must allow the person to remove products from the cart. Removal must update the cart contents and totals immediately, providing visible feedback.
* **AC 2.2.3 (Empty State)**: The cart must recognize an empty state and display a clear user-facing empty notification. If the cart is empty, the system must prevent proceeding as though a valid purchase existed.
* **AC 2.2.4 (Persistence Boundaries)**: Durable cart persistence across browser closures or separate browser sessions is not mandatory, and mandatory cart persistence in `localStorage` is excluded.

---

## Epic 3: Basic Authentication

### Story 3.1: User Registration, Sign-In, and Sign-Out
* **As a** visitor
* **I want to** create a customer account, sign in, and sign out
* **So that** the system can identify me.

#### Acceptance Criteria:
* **AC 3.1.1 (Minimum Data)**: Registration and sign-in must request only the minimum data necessary to identify a customer.
* **AC 3.1.2 (Session Status Indicators)**: The interface must visibly indicate whether a user session is active and provide a way to sign out.
* **AC 3.1.3 (Form Feedback and Validation)**:
  - Forms must explain the expected information.
  - Forms must validate incomplete or invalid input.
  - Form errors must be communicated safely to help the person understand what is wrong without exposing sensitive internal database, server, or system details.
* **AC 3.1.4 (Secure Credentials)**: Customer passwords must not be displayed or stored as readable plain text.

### Story 3.2: Guide Visitor Identification During Checkout
* **As a** visitor with items in my cart
* **I want to** be guided to register or sign in when proceeding to checkout
* **So that** I can identify myself without losing my active shopping cart context.

#### Acceptance Criteria:
* **AC 3.2.1 (Identification Guide)**: When an unauthenticated visitor attempts to finish the journey (e.g., checkout), the application must guide them to sign in or register.
* **AC 3.2.2 (Cart Context Retention)**: Guiding the buyer to sign in or register must occur without causing an unjustified loss of the active local shopping cart context.

---

## Epic 4: Simulated Checkout

### Story 4.1: Simulated Purchase and Confirmation
* **As a** logged-in customer
* **I want to** review my order and complete a fictitious checkout
* **So that** I can finish the simulated purchase journey.

#### Acceptance Criteria:
* **AC 4.1.1 (Empty Cart Block)**: If the shopping cart is empty, the application must block the user from proceeding to or submitting checkout.
* **AC 4.1.2 (Order Summary)**: Before confirmation, the application must present a clear summary of the products, quantities, and overall accumulated purchase total.
* **AC 4.1.3 (Minimum Demonstration Information)**: The checkout form may request only the minimum demonstration information necessary to complete the journey. It must not implement an address book or the selection of saved addresses.
* **AC 4.1.4 (Fictitious Notice)**: The checkout screen must clearly state that no monetary charges are made and no real payment gateway is contacted.
* **AC 4.1.5 (Simulated Confirmation and Summary)**: Successful completion must present an unambiguous confirmation and a summary of the simulated purchase.
* **AC 4.1.6 (Comprehensible Reset State)**: A successful checkout confirmation must leave the system in a comprehensible state from which a new purchase can be started.
