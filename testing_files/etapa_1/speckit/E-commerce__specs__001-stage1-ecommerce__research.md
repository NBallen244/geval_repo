# Technical Research: Stage 1 E-Commerce Application

This document outlines the technical research and lightweight decisions made to support the implementation of the Stage 1 E-Commerce Application. All choices prioritising the simplest local demonstration approach are defined as technical choices rather than functional requirements.

## Core Technical Choices

### 1. Catalog Data Storage (Technical Choice)
- **Decision**: Catalog data is stored as an in-memory list on the backend component, initialized at startup from a local static JSON file.
- **Rationale**: The canonical seed explicitly permits a simple mechanism appropriate for a demonstration. Using a local JSON file to initialize an in-memory list on the backend separates server-side logic from frontend presentation while avoiding external database server overhead or query-parser management. This ensures data consistency is maintained during moves from catalog to cart and checkout.

### 2. User Account Storage (Technical Choice)
- **Decision**: User accounts are stored in an in-memory dictionary on the backend component, persisting for the duration of the backend process life.
- **Rationale**: This is a simple, zero-setup mechanism appropriate for a demonstration, avoiding database servers or migrations while allowing separate frontend and backend components to communicate over a interface.

### 3. Password Security (Technical Choice)
- **Decision**: The backend utilizes Python's standard library `hashlib.pbkdf2_hmac` with a salt and a fixed iteration count to securely derive password hashes.
- **Rationale**: This technical choice satisfies the exact seed requirement that passwords must not be displayed or stored as readable plain text within the academic scope. It runs locally using Python standard library components without relying on external system library compilation.

### 4. Session, Authentication, & Sign-Out State (Technical Choice)
- **Decision**: Upon successful sign-in, the backend component returns a lightweight session token (UUID or secure string). The client stores this session token in memory to indicate the active session status. 
- **Sign-Out Action**: Ends the active authenticated session by calling the backend to invalidate the session token and clearing it from client-side memory. This visibly returns the interface to a non-authenticated state while preserving the active shopping cart context.
- **Rationale**: Keeps registration and sign-in distinct as supported capabilities while providing a simple, technology-neutral method of authentication and sign-out. Post-registration session behavior is left completely unspecified since the seed does not define it.

### 5. Shopping Cart Management (Technical Choice)
- **Decision**: The shopping cart is managed entirely in React component/context state on the frontend. Durable cart persistence is omitted, as the seed explicitly states that durable cart persistence across browser closures or separate sessions is not mandatory.
- **Rationale**: Provides immediate interface updates and simplifies local state synchronization without introducing complex local cache management.
