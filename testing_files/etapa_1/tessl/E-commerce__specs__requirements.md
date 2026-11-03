# Requirements - Stage 1 E-Commerce

This document establishes the atomic and verifiable functional and non-functional requirements for Stage 1, derived directly from the canonical seed specification.

## 1. Product Catalog (CAT)
- **REQ-CAT-1**: The application must provide a product catalog as the main entry point, accessible to visitors without authentication.
- **REQ-CAT-2**: Each product in the catalog must display its name, a representative image, a short description, its price, and its general availability.
- **REQ-CAT-3**: Demonstration data used in the catalog must remain consistent between the user interface and other application flows.
- **REQ-CAT-4 (Optional)**: The application may include an expanded product view. If included, it must complement the catalog and preserve the identical commercial information (name, image, description, price, and availability).
- **REQ-CAT-5 (Exclusion)**: The catalog must not implement text search, advanced filters, recommendations, or complex catalog classification.

## 2. Local Shopping Cart (CRT)
- **REQ-CRT-1**: A person must be able to add products from the catalog to a shopping cart managed locally by the application.
- **REQ-CRT-2**: The cart must display which products it contains, their quantities, their individual prices, and the accumulated total purchase amount.
- **REQ-CRT-3**: The cart must allow the user to adjust product quantities, remove products, and recognize an empty state.
- **REQ-CRT-4**: Changes to the cart must be reflected immediately in the interface and remain available throughout the active journey.
- **REQ-CRT-5 (Exclusion)**: Durable cart persistence across browser closures or separate sessions is not mandatory and is not required for this stage.

## 3. Basic Authentication (ATH)
- **REQ-ATH-1**: The application must provide a simple customer registration and sign-in mechanism using the minimum necessary data to identify a customer.
- **REQ-ATH-2**: The interface must visibly indicate whether a session is active (authenticated) or inactive.
- **REQ-ATH-3**: The interface must provide a way for the authenticated user to sign out.
- **REQ-ATH-4**: Registration and sign-in forms must explain the expected information, validate incomplete or invalid input, and communicate errors without exposing sensitive information.
- **REQ-ATH-5**: Passwords must be handled securely within the academic scope; they must not be displayed in plain text or stored as readable plain text.
- **REQ-ATH-6 (Exclusion)**: The authentication mechanism must not implement multi-factor authentication, external identity providers, password recovery, email verification, or advanced profile management.
- **REQ-ATH-7**: When an unauthenticated buyer must be identified to finish the purchase journey, the application must guide the buyer to sign in or register and then allow the journey to continue without losing the active cart. Visitors must still be able to browse the catalog and prepare the cart without authentication.

## 4. Simulated Checkout (CHK)
- **REQ-CHK-1**: A person with products in the cart must be allowed to proceed to a simulated checkout.
- **REQ-CHK-2**: Before checkout confirmation, the application must present a clear summary of the products, their quantities, and the total purchase amount.
- **REQ-CHK-3**: The checkout process may request only the minimum demonstration information necessary to complete the simulated journey.
- **REQ-CHK-4**: The payment confirmation must be fictitious. The system must clearly and explicitly state that no actual charge is made and no real payment gateway is contacted.
- **REQ-CHK-5**: After successful completion, the system must present an unambiguous purchase confirmation and a summary of the simulated purchase.
- **REQ-CHK-6**: If the shopping cart is empty, the application must prevent the user from proceeding to checkout.
- **REQ-CHK-7 (Exclusion)**: The checkout must not implement an address book, selection of saved addresses, advanced tax breakdowns, or real payment integrations.

## 5. Continuous Journey & User Experience (UX)
- **REQ-UX-1**: The catalog, cart, authentication, and checkout must operate as one continuous and cohesive journey.
- **REQ-UX-2**: Product information, quantities, and totals must remain consistent when moving across all views (catalog, cart, checkout summary, and confirmation).
- **REQ-UX-3**: User authentication (registration or sign-in) must not cause an unjustified loss of the active cart.
- **REQ-UX-4**: A successful checkout confirmation must leave the system in a comprehensible state from which a new purchase journey can be started.
- **REQ-UX-5**: The application must provide visible feedback for relevant actions, including adding or removing a product, signing in, encountering invalid data, and completing the simulated purchase.
- **REQ-UX-6**: The system must handle loading, empty, and error states sufficiently so the user understands what is happening and what action to take next.
- **REQ-UX-7**: The interface must be clear, consistent, and usable on both desktop and mobile screens.
- **REQ-UX-8**: Primary controls must have understandable names, forms must correctly associate labels and messages, and keyboard navigation must not prevent completion of the main journey.
- **REQ-UX-9**: Visual design must not hide or alter any behavior specified in the canonical seed.

## 6. Technical, Architecture & Language Constraints (TEC)
- **REQ-TEC-1**: The frontend must be implemented with React and TypeScript.
- **REQ-TEC-2**: The backend must be implemented with Python and FastAPI.
- **REQ-TEC-3**: The application must separate user interface logic (frontend) from server-side logic (backend) through a clear communication interface.
- **REQ-TEC-4**: The project structure must allow the frontend and the backend components to be run and reviewed separately.
- **REQ-TEC-5**: The catalog and account data may use a simple mechanism appropriate for a demonstration (e.g., in-memory storage).
- **REQ-TEC-6**: All specification artifacts, source-code identifiers, code comments, technical documentation, and user-facing interface text must be written in English.
- **REQ-TEC-7 (Exclusion)**: Do not implement production infrastructure, distributed services, asynchronous processing, real external integrations, real-time inventory, coupons, multi-criteria filtering, dynamic shipping calculations, reviews, ratings, moderation, multiple currencies, seller/admin functionality, containers, CI/CD, mandatory E2E tests, API caching, or advanced access controls.
