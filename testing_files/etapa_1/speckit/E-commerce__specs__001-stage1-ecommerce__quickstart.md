# Quickstart & Validation Guide (Technical Choice)

This guide describes how to run and validate the Stage 1 E-Commerce Application end-to-end. This is a local demonstration web application with separate frontend and backend components.

## Prerequisites

- **Frontend**: Node.js (compatible local version) and npm.
- **Backend**: Python (compatible local version) and pip.

---

## Component Setup & Run Instructions

Because the frontend and backend run as separate components, they must be started in separate terminal windows. All paths, commands, and local ports are implementation-level interface choices.

### 1. Run the Backend
1. Open a terminal and navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the backend development server (e.g., using uvicorn):
   ```bash
   uvicorn src.main:app --reload --port 8000
   ```

### 2. Run the Frontend
1. Open a separate terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install Node dependencies using npm:
   ```bash
   npm install
   ```
3. Run the frontend development server using npm:
   ```bash
   npm start
   ```

---

## End-to-End Validation Scenario

The following steps define the manual validation scenario for the complete purchasing journey. It validates only the seed-approved behaviors and our chosen technical integration, without prescribing exact UI labels, specific page names, or button text.

### Step 1: Browse the Product Catalog & Interface Usability
- **Action**: Navigate to the catalog interface as an unauthenticated visitor. Resize the screen or test on desktop and mobile viewports. Navigate the elements using the keyboard (e.g., Tab, Enter, Space) and review control associations.
- **Expected Outcome**:
  - The product catalog is displayed and accessible without authentication.
  - You see demonstration products, each displaying its name, a representative image, a short description, price, and general availability.
  - The demonstration data matches consistently between the user interface and the backend.
  - The user interface is clear, consistent, and usable on desktop and mobile screens.
  - Primary controls have understandable names.
  - Forms correctly associate labels and messages.
  - Keyboard navigation does not prevent completion of the main journey.
  - Loading, empty, and error states are handled sufficiently for the person to understand what is happening and what they can do next.

### Step 2: Manage the Local Shopping Cart & Action Feedback
- **Action**: Add a product to the cart, adjust its quantity, and then remove the product. Observe the interface state and any visible notifications or indicators.
- **Expected Outcome**:
  - The shopping cart clearly communicates the products it contains, their quantities, their prices, and the accumulated purchase total.
  - Cart changes are reflected immediately in the interface.
  - The interface allows the person to recognize an empty state.
  - Product information, quantities, and totals remain consistent.
  - The application provides clear visible feedback for relevant actions, specifically for adding a product and removing a product.

### Step 3: Registration and Account Creation
- **Action**: Open the registration interface, input the minimum identification data required to create an account, and submit.
- **Expected Outcome**:
  - An account is successfully created on the backend.
  - Post-registration session behavior is left unspecified.
  - The active local shopping cart context is preserved.

### Step 4: Authentication Form Validation & Session Sign-In
- **Action**: Open the sign-in interface and test the following inputs:
  1. **Incomplete input**: Submit empty fields or partially filled identifiers/passwords.
  2. **Invalid input**: Submit incorrect credentials or malformed details.
  3. **Valid input**: Submit the registered customer identification data.
- **Expected Outcome**:
  - For incomplete input: Authentication forms validate the input, explain the expected information, and handle errors safely by communicating non-sensitive, useful error messages without displaying passwords or storing them as readable plain text.
  - For invalid input: Forms validate the invalid credentials and communicate errors safely without revealing unnecessary internal system details.
  - For valid input: The authenticated session is successfully activated and the interface visibly indicates that the session is active.
  - The application provides visible feedback for signing in and for encountering invalid data (unsuccessful sign-in or form errors).
  - The active local shopping cart context is preserved throughout this identification transition.

### Step 5: Session Sign-Out
- **Action**: Click or trigger the sign-out control while authenticated.
- **Expected Outcome**:
  - The active session is invalidated on the backend and ended locally.
  - The interface visibly returns to a non-authenticated state.
  - The active shopping cart context is preserved (no cart clearing or loss of purchase context occurs upon sign-out).

### Step 6: Simulated Checkout
- **Action**: Proceed to the checkout interface with products in the cart, input the minimum opaque demonstration information required, and submit.
- **Expected Outcome**:
  - If the cart is empty, the application prevents proceeding to checkout.
  - Before confirmation, the interface presents a clear summary of the products, quantities, and total.
  - Submitting the minimum demonstration info results in simulated confirmation and an unambiguous summary of the simulated purchase.
  - The interface clearly states that no charge is made and no real payment gateway is contacted.
  - The application provides clear visible feedback for completing the simulated purchase.
  - Successful confirmation leaves the system in a comprehensible state from which a new purchase can be started.
