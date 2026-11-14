# Story 1.1: Progression Initialization and Unified State Response

**Status:** ready-for-dev
**Epic:** Epic 1 (Authoritative Progression, Multi-Line Scoring, and Difficulty System)
**Story ID:** 1.1

## Overview
As a Software Architect,
I want the game session to initialize and return all 7 progression fields,
So that both client and server have a single authoritative starting state.

## Context
- **Specification:** `_bmad-output/stage2/implementation-artifacts/spec-stage-2-tetris-study.md`
- **Architecture Spine:** `_bmad-output/stage2/planning-artifacts/architecture/stage2-option-a/ARCHITECTURE-SPINE.md`
- **PRD:** `_bmad-output/stage2/planning-artifacts/prds/prd-stage2-option-a/prd.md`

## Acceptance Criteria
- **Given** no active game session,
- **When** `POST /api/games` is executed,
- **Then** a new game session is created with standard board, status `"playing"`, active_piece, and preview next_piece.
- **And** the 7 new fields are returned: `score` is 0, `total_lines` is 0, `level` is 1, `gravity_interval_ms` is 500, `next_piece` is drawn, `hold_piece` is `null`, and `can_hold` is `true`.
- **And** the creation performs exactly 2 random draws (one for active_piece, one for next_piece).
- **And** any standard state read via `GET /api/games/{id}` returns the same 11 fields with zero (0) RNG draws.
