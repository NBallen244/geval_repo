## Why

The goal is to initialize a modern, daily-use, responsive web calculator application. This change is needed to establish the foundational architecture, including the robust FastAPI arithmetic backend and the accessible React/TypeScript frontend client, ensuring accurate arithmetic evaluation and an optimal user experience.

## What Changes

- **Backend Math Evaluation Engine**: Establish a robust, Python-based FastAPI backend that exposes a secure and accurate endpoint (`POST /api/v1/evaluate`) to parse and evaluate chained expressions following PEMDAS rules with high decimal precision using Python's `decimal` module.
- **Frontend Calculator UI/UX**: Develop a responsive, physical-desktop-like React component built with TypeScript, managing the interactive input/expression states, live evaluations, and visual results.
- **Keyboard and Accessibility Integrations**: Deliver full keyboard bindings (digits, operators, evaluate, clear, reset) and screen reader support (using standard ARIA tags and live regions).
- **Project Structure & Testing Pipeline**: Scaffold the directories for both components, along with initial test files in Pytest for backend calculation logic.

## Capabilities

### New Capabilities

- `basic-calculator`: Core capability representing the responsive calculator UI, visual states, and backend evaluation service utilizing FastAPI and exact decimal precision.

### Modified Capabilities

## Impact

- **API Endpoint**: Introduces a new API router and service in the backend exposing `POST /api/v1/evaluate`.
- **Ecosystem**: Introduces standard dependencies for React/TypeScript (Vite, standard npm packages) and Python (FastAPI, pytest, uvicorn).
- **Testing**: Introduces automated testing via `pytest` for calculating math expressions.
