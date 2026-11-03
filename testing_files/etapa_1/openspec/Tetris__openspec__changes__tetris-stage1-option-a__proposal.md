# OpenSpec Proposal: Greenfield Decoupled Browser-Based Tetris Study (Stage 1, Option A)

## 1. Background & Motivation
This proposal establishes the planning foundation for Stage 1 (Option A) of a browser-based Tetris study. This greenfield project aims to implement a decoupled, state-authoritative Python FastAPI backend and a clean, responsive React with TypeScript frontend. To ensure absolute game-play integrity, prevent client-side manipulation, and establish high-signal research metrics, all game rules, tick mechanics, line clearing, and collision boundaries are strictly evaluated and owned by the backend.

## 2. Scope & Boundaries

### 2.1. In-Scope (Stage 1, Option A)
- **Authoritative Backend:** A stateless/in-memory Python FastAPI server that manages game sessions, validates moves, executes gravity ticks, handles collisions, locks pieces, and clears rows.
- **Responsive Frontend:** A React with TypeScript SPA that fetches state, handles local player keyboard controls (left, right, soft drop, restart), and maintains a regular 500 ms gravity tick request interval.
- **Fixed Board Geometry:** A standardized 10-column by 20-row grid using a top-left origin coordinate system.
- **Seven Standard Tetrominoes:** Seven tetrominoes (I, O, T, S, Z, J, L) spawning in their default initial orientations at the top-center of the board.
- **Basic Game Mechanics:** Left/right shifting, soft dropping, collision detection against borders and stacked blocks, lock-down, complete row clearing, and game-over detection.
- **Greenfield Setup:** Simple dependencies (FastAPI, Uvicorn, pytest for backend; Vite, React, TypeScript for frontend).
- **Language Mandate:** 100% English for specifications, application text, UI labels, console messages, tests, and comments.

### 2.2. Out-of-Scope (Stage 1 Non-Goals)
The following features are explicitly excluded from this stage:
- Block rotations and wall kicks.
- Preview of next pieces, ghost pieces, or "hold" slots.
- Hard drop and wall kicks.
- Scoring, line counters, levels, and speed progression (gravity is fixed at 500 ms).
- Databases, user authentication, or persistent accounts.
- Multiplayer, audio effects, or advanced custom styling.

## 3. High-Level Architecture
- **Backend Stack:** FastAPI running on Uvicorn. Game states are kept in memory mapped by UUIDs.
- **Frontend Stack:** React, TypeScript, and Vite.
- **Communication Protocol:** JSON-based REST API over HTTP.

## 4. Key Acceptance Criteria
- **AC-1:** The backend MUST reject any movement that results in a collision with boundaries or settled blocks.
- **AC-2:** The backend MUST identify filled rows, clear them, shift upper rows downward, and spawn the next piece.
- **AC-3:** The backend MUST declare a `game_over` state immediately when a newly spawned piece collides with existing settled blocks.
- **AC-4:** The frontend MUST display a visual grid of 10x20 cells and poll/tick the backend every 500 ms.
