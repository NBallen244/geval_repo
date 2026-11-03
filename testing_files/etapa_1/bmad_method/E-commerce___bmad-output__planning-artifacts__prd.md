# Product Requirements Document (PRD) - Stage 1 E-Commerce Case

## 1. Document Purpose and Scope
This Product Requirements Document (PRD) outlines the requirements for Stage 1 of the E-Commerce Case. It is derived solely from `especificacion-semilla-final-en.md`, which serves as the canonical seed and the only functional source for the project. 

The goal of Stage 1 is to implement an executable, simple, but complete demonstration e-commerce web application that covers the main purchasing journey: browsing products, managing a local cart, registering or signing in, and completing a fictitious checkout.

---

## 2. Core Functional Requirements

### 2.1 Product Catalog
- **Authentication**: Must be accessible to visitors without authentication.
- **Product Information**: Each product must display:
  - Product Name
  - Representative Image
  - Short Description
  - Price
  - General Availability
- **Consistency**: Demonstration data must remain consistent between the user interface and the rest of the application flow.
- **Expanded Product View (Optional)**: If an expanded product view is included, it must complement the catalog and preserve the same commercial information.
- **Exclusions**: This stage does not include text search, advanced filters, recommendations, or complex catalog classification.

### 2.2 Local Shopping Cart
- **Cart Contents**: The cart must communicate which products it contains, their quantities, individual prices, and the accumulated purchase total.
- **Cart Management**: The cart must allow the person to:
  - Add products to the cart.
  - Adjust quantities.
  - Remove products.
  - Recognize an empty state.
- **Interface Responsiveness**: Changes must be reflected immediately in the interface and remain available throughout the person's active journey.
- **Persistence Boundary**: 
  - Durable cart persistence across browser closures or separate browser sessions is not part of this stage and must not be treated as mandatory.
  - Mandatory cart persistence in `localStorage` is excluded.

### 2.3 Basic Authentication
- **Mechanism**: Simple registration, sign-in, and sign-out.
- **Inputs**: Use only the minimum data necessary to identify a customer.
- **Session Indicators**: The interface must visibly indicate whether a session is active and provide a way to sign out.
- **Forms and Error Handling**:
  - Forms must explain the expected information.
  - Validate incomplete or invalid input.
  - Communicate errors without exposing sensitive information.
- **Journey Integration**:
  - When the buyer must be identified to finish the journey, the application must guide them to sign in or register.
  - This step must occur without losing the active purchase context.
- **Exclusions**: This stage does not include multi-factor authentication, external identity providers, password recovery, email verification, or advanced profile management.

### 2.4 Simulated Checkout
- **Prerequisites**: If the cart is empty, the application must not allow the person to proceed as though a valid purchase existed.
- **Checkout Summary**: Before confirmation, present a clear summary of the products, quantities, and total.
- **Checkout Inputs**: Request only the minimum demonstration information necessary to complete the journey. It must not implement an address book or the selection of saved addresses.
- **Fictitious Payment**: 
  - Payment confirmation is fictitious.
  - The system must clearly state that no charge is made and no real payment gateway is contacted.
- **Order Confirmation**: After successful completion, present an unambiguous confirmation and a summary of the simulated purchase.
- **Next Steps**: A successful confirmation must leave the system in a comprehensible state from which a new purchase can be started.

---

## 3. General Experience & Non-Functional Requirements

### 3.1 Interface Usability and Responsiveness
- **Multi-device Usability**: The interface must be clear, consistent, and usable on desktop and mobile screens.
- **Accessibility & Controls**: Primary controls must have understandable names, forms must correctly associate labels and messages, and keyboard navigation must not prevent completion of the main journey.
- **Visual Clarity**: Visual design may vary between implementations, but it must not hide or alter the behavior described in this document.
- **Feedback Loop**: Provide visible feedback for relevant actions, including:
  - Adding or removing a product.
  - Signing in.
  - Encountering invalid data.
  - Completing the simulated purchase.
  - Loading, empty, and error states must be handled sufficiently for the person to understand what is happening and what they can do next.

### 3.2 Security and Academic Constraints
- **Credential Storage**: Passwords must not be displayed or stored as readable plain text.
- **Information Disclosure**: Error messages must be useful without revealing unnecessary internal system details.

---

## 4. Required Technologies and Architecture
- **Frontend Stack**: React and TypeScript.
- **Backend Stack**: Python and FastAPI.
- **Separation of Concerns**: Separate the user interface from server-side logic. The frontend and backend must communicate through a clear interface so that presentation, business logic, and data access are not mixed unnecessarily.
- **Execution Separation**: The project structure must allow the frontend and backend to be run and reviewed separately.
- **Data Storage**: Catalog and account data may use a simple mechanism appropriate for a demonstration.
- **Language**: All generated specification artifacts, source-code identifiers, code comments, technical documentation, and user-facing interface text must be written in English.

---

## 5. Stage Boundaries and Exclusions
The scope ends with a simulated purchase and excludes capabilities reserved for later stages or other case-study options.

Do not implement:
- Quick text search or mandatory cart persistence in `localStorage`.
- Address selection or management, or an advanced tax breakdown.
- Real payments, card storage, or payment-gateway integration.
- Real-time inventory, coupons, multi-criteria filtering, or dynamic shipping calculations.
- Reviews, ratings, moderation, or support for multiple currencies.
- Seller or administrator functionality.
- Containers, continuous integration or deployment, mandatory end-to-end tests, API caching, or advanced access controls.
