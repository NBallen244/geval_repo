# System Architecture Documentation: Tetris Core

This document summarizes the high-level architecture and implementation decisions for the decoupled single-player Tetris Core.

## Decoupled Web Architecture

The project consists of two completely independent applications:
1. **Authoritative REST Backend** (`backend/`): Built with Python, FastAPI, and Pydantic. It holds the game logic, boards, pieces, collision checking, locking, and line-clearing entirely in-memory.
2. **Visual Client Frontend** (`frontend/`): Built with React 18, TypeScript, and Vite. It is a client-side single-page application that renders the board, captures user inputs, and triggers gravity ticks at a fixed 500 ms interval.

```text
+-----------------------+              HTTP Requests              +--------------------------+
|                       |  ------------------------------------>  |                          |
|    React Frontend     |                                         |     FastAPI Backend      |
|  (State presentation) |  <------------------------------------  | (Authoritative engine &  |
|                       |             JSON Responses              |      session store)      |
+-----------------------+                                         +--------------------------+
```

## Key Architectural Decisions

- **Server-Owned Rules**: The backend completely validates all coordinates, boundaries, and collisions. This prevents client tampering and ensures high testability of the core game rules.
- **Stateless Gravity Ticks**: The backend doesn't run thread-based game timers. Instead, the frontend owns the primary clock (`500 ms` interval) and sends gravity tick requests to the server, which simplifies server concurrency.
- **In-Memory Store**: Game sessions are held in a global Python dictionary mapped to unique UUIDs. No database or state persistence is used.
- **Vanilla CSS Grid**: Used for board layout and block visual design. No CSS frameworks are used, maintaining compliance with project principles.
