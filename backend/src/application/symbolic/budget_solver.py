from typing import List, Tuple, Dict, Any
from decimal import Decimal
import structlog
# import z3  # Will be imported inside class to avoid extensive load time issues if unused

logger = structlog.get_logger()

class BudgetSolver:
    """
    Symbolic solver for budget verification using Z3.
    """
    
    def __init__(self):
        try:
            import z3
            self.solver = z3.Solver()
            self._z3 = z3
        except ImportError:
            logger.error("z3_not_installed")
            self.solver = None
            self._z3 = None

    def verify_budget_sum(self, total: Decimal, components: List[Decimal]) -> Tuple[bool, str]:
        """
        Verify that the sum of components equals the total.
        
        Args:
            total: The declared total budget/expense.
            components: List of component amounts.
            
        Returns:
            Tuple (is_valid, proof_or_counterexample_string)
        """
        if not self.solver:
            return False, "Z3 not installed"

        # Create Z3 variables
        # We model this as C1 + C2 + ... + Cn == Total
        # But to be robust against floating point, we convert to int (cents) or use Real
        # Using Reals is safer for general algebraic verification
        
        z_total = self._z3.Real('total')
        z_components = [self._z3.Real(f'c_{i}') for i in range(len(components))]
        
        # Add constraints representing the inputs
        self.solver.reset()
        self.solver.add(z_total == float(total))
        for i, c in enumerate(components):
            self.solver.add(z_components[i] == float(c))
            
        # The property we want to verify is: sum(components) == total
        # We try to prove the negation is UNSAT
        sum_components = sum(z_components)
        
        # Check if it's possible for sum != total
        self.solver.add(sum_components != z_total)
        
        result = self.solver.check()
        
        if result == self._z3.unsat:
            return True, "verified: sum(components) == total holds for all provided values"
        elif result == self._z3.sat:
            model = self.solver.model()
            # In a real counterexample we'd show the values, but here we just used constants
            # so SAT means the inputs themselves violate the constraint (logic error in inputs)
            diff = float(total) - sum(float(c) for c in components)
            return False, f"violation: sum != total (diff: {diff})"
        else:
            return False, "unknown"

    def detect_rule_conflicts(self, rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect logical conflicts between categorization rules.
        Example conflict: Same pattern maps to different categories.
        """
        conflicts = []
        # Group by pattern to find direct conflicts
        # This is a simple symbolic check: if Pattern(x) -> CatA AND Pattern(x) -> CatB, then CatA == CatB must hold
        # If CatA != CatB, we have a contradiction for input x
        
        from collections import defaultdict
        pattern_map = defaultdict(list)
        
        for rule in rules:
            pattern = rule.get('pattern')
            category = rule.get('category')
            if pattern and category:
                pattern_map[pattern].append(category)
                
        for pattern, categories in pattern_map.items():
            unique_cats = set(categories)
            if len(unique_cats) > 1:
                # Symbolic Representation:
                # Let P be the predicate "matches pattern"
                # Rule 1: P -> CatA
                # Rule 2: P -> CatB
                # If CatA != CatB, implies P -> False (Pattern cannot exist validly)
                conflicts.append({
                    "pattern": pattern,
                    "conflicting_categories": list(unique_cats),
                    "reason": "Direct contradiction: Same pattern implies multiple categories"
                })
                
        return conflicts
