## Why

The goal of Stage 4 is to transition the calculator application from traditional infix expression evaluation with standard algebraic precedence (PEMDAS) to stack-based Reverse Polish Notation (RPN) evaluation. 

This drastic architectural refactor tests the capability of Spec-Driven Development to handle breaking changes. It decouples operators from parentheses, simplifies complex expression parsing, and introduces standard dual-mode input workflows and a real-time visual stack display to improve the user experience for complex math computations.

## What Changes

- **Core Backend Evaluation Refactor**: Re-architect the core mathematical engine to evaluate expressions via Reverse Polish Notation (RPN) / Postfix tokens. The backend will parse standard expressions using the Shunting Yard Algorithm into Postfix representation or directly evaluate Postfix tokens using a stack-based engine.
- **Support for RPN Input Workflows**: Introduce a dual standard/RPN mode in the frontend. In RPN mode, input digits can be pushed directly to the stack using a dedicated `ENTER` key.
- **Real-Time Stack Visualizer**: Add a visual stack indicator/display to the React frontend to show the current levels of the evaluation stack ($X, Y, Z, T$, etc.) in real-time.
- **Exact Decimal Precision Preservation**: Ensure stack operations (pushes, pops, computations) maintain exact `Decimal` precision matching Stage 1 requirements.
- **Scientific Operator Adaptations**: Adapt scientific operators, constants, and functions (introduced in Stage 2) to evaluate via stack-based operations (pushing operands, executing unary functions like `sin`, `ln`, `sqrt`, and binary operations like `root`, power).
- **Test Suite Updates**: Refactor the test suite to validate RPN tokenization, stack push/pop operations, stack operator evaluation, and error handling (e.g. stack underflow, insufficient operands) while maintaining at least 80% statement and branch coverage.

## Capabilities

### New Capabilities
- None (All work is built upon refactoring existing calculator structures)

### Modified Capabilities
- `basic-calculator`: The core algebraic parsing engine is replaced with RPN/Postfix logic. The UI adapts to support dual standard/RPN entry modes and displays active stack levels ($X, Y, Z, T$) with a dedicated virtual and physical `ENTER` key.
- `scientific-calculator`: Scientific mathematical functions and constants are refactored to evaluate via stack operations, pushing operands and calling unary or binary scientific operations.

## Impact

- **Backend (FastAPI)**: Refactor `app/calculator.py` and endpoint inputs in `app/main.py` to accept, parse, and evaluate RPN expressions.
- **Frontend (React)**: Update `src/App.tsx` state management to support active evaluation stacks, add keyboard listener mappings for `Enter` to push to stack, and add a CSS/HTML layout block for displaying the active stack.
- **Tests**: Refactor `backend/tests/test_calculator.py` and frontend test suites to align with RPN rules, ensuring statement/branch coverage remains strictly $\ge 80\%$.
- **Docker Setup**: Ensure both service containers build and run successfully with the new RPN-centric architecture.
