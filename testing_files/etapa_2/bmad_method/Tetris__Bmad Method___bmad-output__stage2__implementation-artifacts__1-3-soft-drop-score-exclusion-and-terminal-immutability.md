# Story 1.3: Soft Drop Score Exclusion and Terminal Immutability

**Status:** ready-for-dev
**Epic:** Epic 1 (Authoritative Progression, Multi-Line Scoring, and Difficulty System)
**Story ID:** 1.3

## Overview
As a Security Reviewer,
I want downward movements to grant no score and terminal states to be completely immutable,
So that scoring integrity is maintained and no post-gameover mutations occur.

## Context
- **Specification:** `_bmad-output/stage2/implementation-artifacts/spec-stage-2-tetris-study.md`
- **Architecture Spine:** `_bmad-output/stage2/planning-artifacts/architecture/stage2-option-a/ARCHITECTURE-SPINE.md`
- **PRD:** `_bmad-output/stage2/planning-artifacts/prds/prd-stage2-option-a/prd.md`

## Acceptance Criteria
- **Given** an active game session,
- **When** a `POST /api/games/{id}/move` with direction `"down"` is processed,
- **Then** the active piece advances rows, but the score is NOT incremented (remains unchanged).
- **Given** a game session with status `"game_over"`,
- **When** any `POST` move/tick/hold request or `GET` request is received,
- **Then** the endpoint returns the exact current state unmodified and performs exactly zero (0) RNG draws.
