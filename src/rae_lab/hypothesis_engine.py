from rae_core.models.improvement import Hypothesis
from rae_core.models.failure import FailureLearningRecord
from rae_core.models.evidence import OutcomeRecord
from typing import List
import logging

logger = logging.getLogger(__name__)

class HypothesisEngine:
    def generate_from_failures(self, failures: List[FailureLearningRecord]) -> List[Hypothesis]:
        hypotheses = []
        by_type = {}
        for f in failures:
            by_type.setdefault(f.failure_type, []).append(f)

        for failure_type, records in by_type.items():
            if len(records) >= 2:
                h = Hypothesis(
                    statement=f"Zmiana guardrail dla '{failure_type}' zredukuje powtórzenia.",
                    motivation=f"Wzorzec wykryty {len(records)}x. Lekcja: {records[0].lesson_learned}",
                    target_metric="failure_rate"
                )
                hypotheses.append(h)
        return hypotheses

    def generate_from_outcomes(self, outcomes: List[OutcomeRecord]) -> List[Hypothesis]:
        failures = [o for o in outcomes if o.result == "failure"]
        failure_rate = len(failures) / max(len(outcomes), 1)
        if failure_rate > 0.15:
            return [Hypothesis(
                statement="Wysoki failure rate sugeruje problem z obecną strategią.",
                motivation=f"Failure rate: {failure_rate:.1%} (próg: 15%)",
                target_metric="success_rate"
            )]
        return []
