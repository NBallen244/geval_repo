# Story 1.2: Multi-Line Scoring, Level Progression, and Gravity Intervals

**Status:** ready-for-dev
**Epic:** Epic 1 (Authoritative Progression, Multi-Line Scoring, and Difficulty System)
**Story ID:** 1.2

## Overview
As a Developer,
I want the game engine to calculate scores and speed up gravity automatically when completed rows are cleared upon a piece lock,
So that difficulty increases progressively as the player clears lines.

## Context
- **Specification:** `_bmad-output/stage2/implementation-artifacts/spec-stage-2-tetris-study.md`
- **Architecture Spine:** `_bmad-output/stage2/planning-artifacts/architecture/stage2-option-a/ARCHITECTURE-SPINE.md`
- **PRD:** `_bmad-output/stage2/planning-artifacts/prds/prd-stage2-option-a/prd.md`

## Acceptance Criteria
- **Given** an active game session at level $L$,
- **When** a piece locks and clears $R$ rows (where $1 \leq R \leq 4$),
- **Then** the engine awards points to `score` immediately using the pre-lock level $L$ multiplier: 100 points for $R=1$, 300 points for $R=2$, 500 points for $R=3$, or 800 points for $R=4$ (multiplied by $L$).
- **And** the cleared rows are added to the cumulative count: `total_lines = total_lines + R`.
- **And** the current level is updated: `level = 1 + floor(total_lines / 10)`.
- **And** the gravity interval is updated: `gravity_interval_ms = max(100, 500 - 50 * (level - 1))`.
- **And** locking with 0 rows cleared awards 0 points and makes no state adjustments.
- **And** normal piece lock consumes the previewed `next_piece` and draws exactly one (1) new preview piece.
