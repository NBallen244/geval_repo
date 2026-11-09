---
title: Epic 3 - Advanced Scientific Mathematics Context
type: context
created: 2026-10-20
status: done
review_loop_iteration: 0
context: []
---

## Context Overview

Epic 3 transitions the mathematical engine of the web calculator from standard basic arithmetic (`+`, `-`, `*`, `/`) to full advanced scientific features. It introduces support for trigonometric functions with degrees/radians units, base-10 and natural logarithms, power exponents ($x^y$), roots ($\sqrt{x}$), and mathematical constants ($\pi$ and $e$), while strictly enforcing custom mathematical domain boundaries and preventing code injections.

## Architecture & Integration

All evaluations are processed in `backend/app/engine/evaluator.py` via an extended AST `NodeVisitor` subclass, ensuring that all operations are verified securely at compile-time prior to executing any evaluations.
