---
topic: Browser-based Tetris Study
goal: Build Stage 1, Option A of a browser-based Tetris study as a greenfield project.
updated: 2026-10-05T23:54
---

- (decision) Chose Python FastAPI for backend and React with TypeScript for frontend
- (decision) Defined strict single source of truth: all game state, rules, collisions, line clears, and game-over logic are authoritative on backend
- (decision) Set API endpoints contract: POST /api/games, GET /api/games/{id}, POST /api/games/{id}/tick, and POST /api/games/{id}/move
- (decision) Defined game grid as 10 columns by 20 rows, in-memory state storage, and no database or authentication
- (decision) Restricted frontend controls to left, right, and soft drop (down) in Stage 1
- (decision) Set a fixed gravity tick rate of 500ms managed by the client-side timer
- (decision) Explicitly excluded rotation, wall kicks, line counter, score, preview, and hold features from Stage 1 to focus on core decoupled architecture
- (decision) Established English as the universal language for specifications, code, comments, and tests
- (decision) Committed to high backend game rule unit test coverage as a quality standard
- (event) Created product brief brief.md with 30 atomic testable requirements and explicit acceptance criteria
- (event) Corrected brief and PRD to remove unrequested A/D/S/R keyboard controls and 100% test coverage promise; restricted movement to standard ArrowLeft, ArrowRight, and ArrowDown and added visible restart button.
