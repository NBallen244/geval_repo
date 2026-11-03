# Tasks

## 1. Project Scaffolding & Setup

- [x] 1.1 Scaffold backend Python FastAPI application, configure virtual environment, install requirements (fastapi, uvicorn, sqlalchemy, passlib, bcrypt), and verify backend server starts on port 8000 with a health-check route.
- [x] 1.2 Scaffold frontend React application using Vite + TypeScript, install dependencies (react-router-dom, tailwindcss or standard CSS), and verify development server runs on port 5173 with a basic index page.

## 2. Backend Database & Catalog API

- [x] 2.1 Set up SQLite database connection using SQLAlchemy ORM, define schemas for Users and Products, seed the database with consistent demonstration product data, and verify the SQLite file is created and seeded.
- [x] 2.2 Implement `/api/products` GET endpoint to fetch the catalog and, only if the optional expanded product view is included, implement `/api/products/{id}` to fetch its details. Omitting both the expanded view and `/api/products/{id}` still satisfies Stage 1 acceptance. Verify every implemented endpoint returns product data consistent with the application journey.

## 3. Backend Authentication API

- [x] 3.1 Implement security helpers for password hashing using bcrypt (`passlib`) and JWT/session token generation, and verify passwords are never logged or stored as plain text.
- [x] 3.2 Implement `/api/auth/register` and `/api/auth/login` POST endpoints, validate incomplete or invalid input according to the expectations clearly presented by the forms, and verify registration, duplicate-user prevention, and login validation flows return appropriate HTTP status codes.

## 4. Frontend State & Contexts

- [x] 4.1 Implement Cart Context in React to manage add-to-cart, increase/decrease quantities, item deletion, empty-cart checks, and total calculations, and verify cart updates are instantly visible across subscribers and remain consistent.
- [x] 4.2 Implement Session/Auth Context in React to hold the minimum session identity information strictly in memory (without localStorage or durable client-side persistence), integrated with login/register endpoints, and verify local cart state is not lost or wiped upon successful session activation.

## 5. Frontend UI Components & Forms

- [x] 5.1 Implement responsive Header Navigation displaying the active session indicator, clearly named navigation and sign-out controls, and a real-time cart item counter, and verify the layout renders on desktop and mobile.
- [x] 5.2 Implement Product Catalog page displaying product list with name, image, description, price, availability status, and "Add to Cart" button, and verify clicking the button adds the item to local cart and displays visible feedback.
- [x] 5.3 Implement Shopping Cart view with quantity adjusters, item removal triggers, total calculation, and empty state visual handler, and verify changes instantly reflect in the UI.
- [x] 5.4 Implement Registration and Sign-In forms with clear validation messages, correct input-to-label associations, and error messages for incomplete or invalid input. Verify the forms cannot be submitted with incomplete or invalid information according to the expectations they clearly present, and verify keyboard navigation and understandable control names across all forms.

## 6. Checkout Flow & End-to-End Verification

- [x] 6.1 Implement the Checkout summary view displaying final items, quantities, and totals, requesting no more than the minimum demonstration information necessary to complete the journey, and verify an empty cart blocks entry to this view.
- [x] 6.2 Implement Simulated Purchase confirmation page detailing fictitious gateway notice and purchase summary, and verify confirming the purchase clears the local cart and leaves the system in a clean state to start a new purchase.
- [x] 6.3 Implement and verify understandable loading states while catalog data or authentication operations are in progress.
- [x] 6.4 Implement and verify clear absence and empty states for an empty catalog and empty shopping cart.
- [x] 6.5 Implement and verify clear recoverable-error messages explaining the available retry or next action.
- [x] 6.6 Implement and verify guided authentication with cart preservation when an active-cart visitor is directed to sign in or register before checkout.
- [x] 6.7 Verify that product information, quantities, and totals remain consistent across catalog, cart, checkout, and confirmation, and that user-initiated cart changes appear immediately.
- [x] 6.8 Verify understandable primary-control names, correct label/input/message associations, and unblocked keyboard completion of the complete purchasing journey.
- [x] 6.9 Audit and verify that all source-code identifiers, code comments, technical documentation, and user-facing interface text are written in English.
- [x] 6.10 Refactor the simulated checkout notice to be purely informational, removing the mandatory acknowledgment checkbox or any additional mandatory fields prior to confirmation.
- [x] 6.11 Clean up the simulated purchase confirmation notice to render as standard accessible HTML/interface content, removing literal Markdown markers (such as `**`).
