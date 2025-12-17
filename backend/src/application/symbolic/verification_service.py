from typing import List, Dict, Any, Tuple, Optional
import structlog
from src.application.symbolic.budget_solver import BudgetSolver

logger = structlog.get_logger()

class VerificationService:
    """
    Symbolic Verification Service using Z3 (via BudgetSolver).
    Validates static budget constraints and temporal properties.
    """
    def __init__(self):
        self.solver = BudgetSolver()
        self._z3 = self.solver._z3

    def verify_static_constraint(self, total: float, parts: List[float]) -> Tuple[bool, str]:
        """
        Verify static sum constraint: sum(parts) == total.
        Uses 5s timeout.
        """
        s = self._z3.Solver()
        s.set("timeout", 5000) # 5s timeout
        
        # We want to prove: Sum(parts) == Total
        # Negation: Sum(parts) != Total
        # If Negation is UNSAT, then theorem holds.
        
        # Floating point handling: Allow small epsilon
        epsilon = 0.01
        
        # Z3 Real Variables
        Total = self._z3.Real('Total')
        Parts = [self._z3.Real(f'P_{i}') for i in range(len(parts))]
        
        # Bind values
        s.add(Total == total)
        for i, val in enumerate(parts):
            s.add(Parts[i] == val)
            
        # Negation: abs(Sum - Total) > epsilon
        sum_expr = sum(Parts)
        s.add(self._z3.Or(sum_expr > Total + epsilon, sum_expr < Total - epsilon))
        
        result = s.check()
        if result == self._z3.unsat:
            return True, "Z3 Verified: Sum(Parts) == Total"
        elif result == self._z3.sat:
            return False, "Z3 Failed: Sum(Parts) != Total"
        else:
            return False, "Z3 Timeout or Unknown"

    def verify_derived_constraint(self, derived_val: float, context_vals: Dict[str, float], operation: str) -> Tuple[bool, str]:
        """
        Verify constraints like Averages, Percentages, Ratios.
        Args:
            derived_val: The value claimed (e.g., 25.0 for %)
            context_vals: The supporting values (e.g., {'part': 25, 'total': 100})
            operation: 'percentage', 'average', 'ratio'
        """
        if not self._z3: return False, "Z3 Missing"
        
        s = self._z3.Solver()
        s.set("timeout", 5000)
        epsilon = 0.1 # Looser for derived metrics
        
        Claim = self._z3.Real('Claim')
        s.add(Claim == derived_val)
        
        negation = None
        
        if operation == "percentage":
            # Claim (Pct) = (Part / Total) * 100
            # Prove: Claim * Total == Part * 100
            part = context_vals.get('part', 0)
            total = context_vals.get('total', 1) # Avoid div by zero in formulation
            if total == 0: return False, "Total cannot be 0"
            
            Part = self._z3.Real('Part')
            Total = self._z3.Real('Total')
            s.add(Part == part, Total == total)
            
            # Negation: abs(Claim * Total - Part * 100) > epsilon * Total
            # (Scaling epsilon by Total to handle magnitude)
            lhs = Claim * Total
            rhs = Part * 100
            diff = lhs - rhs
            s.add(self._z3.Or(diff > epsilon * Total, diff < -epsilon * Total))
            
        elif operation == "average":
            # Claim (Avg) = Total / Count
            # Prove: Claim * Count == Total
            total = context_vals.get('total', 0)
            count = context_vals.get('count', 1)
            
            Total_Var = self._z3.Real('Total')
            Count_Var = self._z3.Real('Count')
            s.add(Total_Var == total, Count_Var == count)
            
            lhs = Claim * Count_Var
            rhs = Total_Var
            diff = lhs - rhs
            s.add(self._z3.Or(diff > epsilon * count, diff < -epsilon * count))
            
        elif operation == "ratio":
            # Claim (Ratio) = A / B
            # Prove: Claim * B == A
            a = context_vals.get('numerator', 0)
            b = context_vals.get('denominator', 1)
            
            A_Var = self._z3.Real('A')
            B_Var = self._z3.Real('B')
            s.add(A_Var == a, B_Var == b)
            
            lhs = Claim * B_Var
            rhs = A_Var
            diff = lhs - rhs
            s.add(self._z3.Or(diff > epsilon, diff < -epsilon))

        elif operation == "inequality_gt":
            # Claim > Target
            # Negation: Claim <= Target
            target = context_vals.get('target', 0)
            Target_Var = self._z3.Real('Target')
            s.add(Target_Var == target)
            s.add(Claim <= Target_Var) # Negation

        elif operation == "inequality_lt":
            # Claim < Target
            # Negation: Claim >= Target
            target = context_vals.get('target', 0)
            Target_Var = self._z3.Real('Target')
            s.add(Target_Var == target)
            s.add(Claim >= Target_Var) # Negation

        elif operation == "range":
            # Min < Claim < Max
            # Negation: Claim <= Min OR Claim >= Max
            min_val = context_vals.get('min', float('-inf'))
            max_val = context_vals.get('max', float('inf'))
            Min_Var = self._z3.Real('Min')
            Max_Var = self._z3.Real('Max')
            s.add(Min_Var == min_val, Max_Var == max_val)
            
            s.add(self._z3.Or(Claim <= Min_Var, Claim >= Max_Var)) # Negation

        elif operation == "trend_percentage":
            # Claim (Pct) = ((Current - Previous) / Previous) * 100
            # Prove: Claim * Previous == (Current - Previous) * 100
            curr = context_vals.get('current', 0)
            prev = context_vals.get('previous', 1) # Avoid 0
            if prev == 0: return False, "Previous value is 0"
            
            Curr_Var = self._z3.Real('Current')
            Prev_Var = self._z3.Real('Previous')
            s.add(Curr_Var == curr, Prev_Var == prev)
            
            lhs = Claim * Prev_Var
            rhs = (Curr_Var - Prev_Var) * 100
            diff = lhs - rhs
            s.add(self._z3.Or(diff > epsilon * prev, diff < -epsilon * prev))
            
        else:
            return False, f"Unknown op {operation}"
            
        import math
        
        result = s.check()
        if result == self._z3.unsat:
            return True, f"Z3 Verified: {operation} consistency"
        elif result == self._z3.sat:
            return False, f"Z3 Failed: {operation} mismatch"
        else:
            # Fallback: Graceful Degradation to Python Math
            # Cat 9.5: "Graceful degradation"
            # If Z3 times out, we use standard Python float checks
            try:
                passed_fallback = False
                if operation == "percentage":
                    expected = (context_vals['part'] / context_vals['total']) * 100 if context_vals.get('total') else 0
                    passed_fallback = math.isclose(derived_val, expected, abs_tol=0.1)
                elif operation == "average":
                    expected = context_vals['total'] / context_vals['count'] if context_vals.get('count') else 0
                    passed_fallback = math.isclose(derived_val, expected, abs_tol=0.1)
                elif operation == "inequality_gt":
                     passed_fallback = derived_val > context_vals['target']
                elif operation == "inequality_lt":
                     passed_fallback = derived_val < context_vals['target']
                elif operation == "range":
                     passed_fallback = context_vals['min'] < derived_val < context_vals['max']
                
                status_msg = "Fallback Verified" if passed_fallback else "Fallback Failed"
                return passed_fallback, f"Z3 Timeout -> {status_msg}"
            except Exception as e:
                return False, f"Z3 Timeout & Fallback Error: {str(e)}"

    def verify_temporal_property(self, history: List[float], property_type: str, threshold: float) -> Tuple[bool, str]:
        """
        Verify temporal properties over a sequence of values.
        """
        if not self._z3: return False, "Z3 not installed"
        
        s = self._z3.Solver()
        s.set("timeout", 5000)
        
        V = [self._z3.Real(f'V_{i}') for i in range(len(history))]
        for i, val in enumerate(history):
            s.add(V[i] == val)
            
        negation = None
        if property_type == 'never_exceeds':
            conditions = [V[i] > threshold for i in range(len(history))]
            negation = self._z3.Or(conditions)
        elif property_type == 'always_increases':
            conditions = [V[i+1] < V[i] for i in range(len(history) - 1)]
            negation = self._z3.Or(conditions)

        if negation is None: return False, "Unknown prop"
            
        s.add(negation)
        result = s.check()
        
        if result == self._z3.unsat:
            return True, f"Verified: {property_type} holds"
        elif result == self._z3.sat:
             # Find violation
             return False, f"Violation: {property_type} failed"
        else:
            return False, "Timeout"
