# failure_mining_engine.py
try:
    from rae_core.models.failure import FailureLearningRecord
    from rae_core.models.improvement import FailurePatternPack
except ImportError:
    try:
        from rae_libs.rae_core.models.failure import FailureLearningRecord
        from rae_libs.rae_core.models.improvement import FailurePatternPack
    except ImportError:
        # Generic mock fallback for sandboxed offline run
        class FailureLearningRecord:
            def __init__(self):
                self.failure_id = "mock"
                self.failure_type = "mock"
                self.wasted_cost = 0.0
                self.future_guardrail = "mock"
                self.retry_recommendation = "mock"
        class FailurePatternPack:
            def __init__(self, **kwargs): pass

from typing import List
from collections import Counter
import uuid

class FailureMiningEngine:
    MIN_PATTERN_COUNT = 2
    HIGH_COST_THRESHOLD = 50.0

    def mine(self, records: List[FailureLearningRecord]) -> FailurePatternPack:
        type_counts = Counter(r.failure_type for r in records)
        recurring = {t: c for t, c in type_counts.items() if c >= self.MIN_PATTERN_COUNT}
        
        patterns = []
        for f_type, freq in recurring.items():
            sample = next(r for r in records if r.failure_type == f_type)
            avg_cost = sum(r.wasted_cost or 0 for r in records if r.failure_type == f_type) / freq
            patterns.append({
                "pattern": f_type,
                "frequency": freq,
                "guardrail": getattr(sample, "future_guardrail", "undefined"),
                "retry_recommendation": getattr(sample, "retry_recommendation", "manual review"),
                "avg_cost": avg_cost
            })
            
        try:
            return FailurePatternPack(
                patterns=patterns,
                source_failures=[r.failure_id for r in records]
            )
        except Exception:
            return {"patterns": patterns, "source_failures": [getattr(r, "failure_id", "mock") for r in records]}
