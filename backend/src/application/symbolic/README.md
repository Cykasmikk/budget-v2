# Symbolic Module

This module contains symbolic reasoning components using Formal Methods (Z3).

## Components

### BudgetSolver
- **Purpose**: Verifies mathematical invariants and detects logical conflicts using SMT solving (`z3-solver`).
- **Capabilities**:
  - `verify_budget_sum`: Proves that sum of components equals total (or finds counterexample).
  - `detect_rule_conflicts`: Identifies contradictory categorization rules (e.g. same pattern -> different categories).

- **Usage**:
  ```python
  solver = BudgetSolver()
  valid, proof = solver.verify_budget_sum(total, components)
  ```
