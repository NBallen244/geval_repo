# Specification Quality Checklist: Extend Tetris to Stage 2

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-10-20
**Feature**: [specs/002-extend-tetris-stage2/spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable and verifiable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- **2026-10-20 Revision**: Revised specification to align with the authoritative study control seed constraints:
  - Ensured every game-state response uses the exact snake_case JSON keys: `score`, `total_lines`, `level`, `gravity_interval_ms`, `next_piece`, `hold_piece`, and `can_hold`.
  - Preserved the existing Stage 1 `activePiece` legacy camelCase key, mapped to the existing tetromino object.
  - Represented `next_piece` and `hold_piece` as single-letter tetromino type strings (`I`, `O`, `T`, `S`, `Z`, `J`, `L`), with `hold_piece` being nullable.
  - Removed all arbitrary and unmeasurable performance criteria (such as 10 ms timer drift, 50 ms endpoint latency, 100 ms UI latency) and replaced them with functional, verifiable success criteria tied to the seed constraints.
  - Retained the exact Stage 1 random piece generation model, without imposing any equal random shape probabilities beyond fresh random generation.
  - Retained the exact scoring and Hold rules as specified by the study control seed.

## Native Quality & SonarQube Baseline Requirements
- [x] **Documented 404 responses**: All endpoints throwing `HTTPException` with status 404 MUST document this status in their Pydantic/FastAPI `responses` parameter (`python:S8415`).
- [x] **Suitable Random Generator**: The python backend MUST use a cryptographically secure random generator or safe random source (e.g. `secrets.choice` or similar) without suppressions (`python:S2245`).
- [x] **Optional Chaining**: Frontend TypeScript files (e.g., `App.tsx`, `useGame.ts`) MUST prefer optional chaining expressions (`?.`) for concise and readable access (`typescript:S6582`).
- [x] **Stable React Keys**: Board cell/row rendering in `Board.tsx` MUST use stable keys instead of array indices to avoid React key code smells (`typescript:S6479`).
- [x] **Readable Contrast**: CSS styling in `index.css` MUST meet minimal contrast requirements for accessibility (`css:S7924`).
- [x] **Audit & Coverage**: Maintain backend XML coverage, frontend LCOV coverage, and execute dependency audits.

All checklist items have passed. No `[NEEDS CLARIFICATION]` markers exist. The specification is fully revised and ready for planning!
