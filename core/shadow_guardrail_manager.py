# core/shadow_guardrail_manager.py
import re
import uuid
import logging
from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class GuardrailStatus(str, Enum):
    CANDIDATE = "candidate"  # Shadow Mode
    ACTIVE = "active"        # Blocking/Enforced Mode
    REJECTED = "rejected"

class GuardrailRule(BaseModel):
    schema_version: str = "1.0"
    rule_id: str
    pattern: str = Field(..., description="Regex pattern to detect threats")
    description: str
    status: GuardrailStatus = GuardrailStatus.CANDIDATE
    false_positives: int = 0
    total_evaluations: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    evaluated_hours: float = 0.0

class ShadowGuardrailManager:
    """
    Manages Shadow Mode Candidate Guardrails for rae-lab.
    Evaluates rules against historical replay logs over a 72-hour window,
    monitors False Positive rates, prevents policy conflicts,
    and automatically promotes compliant rules to Active.
    """
    def __init__(self, storage_path: str):
        self.rules_file = storage_path
        self.rules: Dict[str, GuardrailRule] = {}
        self._load_rules()

    def _load_rules(self):
        # Programmatic memory load or file persist
        pass

    def register_candidate_rule(self, pattern: str, description: str) -> str:
        """Registers a newly generated security rule as a CANDIDATE in Shadow Mode."""
        rule_id = f"grd_{uuid.uuid4().hex[:12]}"
        rule = GuardrailRule(
            rule_id=rule_id,
            pattern=pattern,
            description=description,
            status=GuardrailStatus.CANDIDATE
        )
        self.rules[rule_id] = rule
        logger.info(f"shadow_guardrail_registered: Rule {rule_id} in CANDIDATE (Shadow) Mode.")
        return rule_id

    def evaluate_rule_on_log(self, rule_id: str, log_message: str, is_actually_malicious: bool) -> bool:
        """
        Evaluates a candidate rule on a log entry. 
        Increments False Positives if it triggers on clean content.
        """
        rule = self.rules.get(rule_id)
        if not rule:
            raise ValueError(f"Rule {rule_id} not found.")

        triggered = False
        try:
            triggered = bool(re.search(rule.pattern, log_message))
        except re.error as e:
            logger.error(f"invalid_regex_pattern in rule {rule_id}: {e}")
            return False

        rule.total_evaluations += 1
        
        # Triggered on clean content -> False Positive!
        if triggered and not is_actually_malicious:
            rule.false_positives += 1
            logger.warning(f"shadow_guardrail_false_positive: Rule {rule_id} matched safe content: '{log_message}'")
            
        return triggered

    def get_false_positive_rate(self, rule_id: str) -> float:
        rule = self.rules.get(rule_id)
        if not rule or rule.total_evaluations == 0:
            return 0.0
        return rule.false_positives / rule.total_evaluations

    def simulate_72h_replay(self, rule_id: str, replay_logs: List[Tuple[str, bool]]) -> Dict[str, Any]:
        """
        Simulates log evaluation over a minimum 72-hour period.
        Logs: List of (log_message, is_actually_malicious)
        """
        rule = self.rules.get(rule_id)
        if not rule:
            raise ValueError(f"Rule {rule_id} not found.")

        for msg, is_malicious in replay_logs:
            self.evaluate_rule_on_log(rule_id, msg, is_malicious)

        # Mark 72 hours of evaluation
        rule.evaluated_hours += 72.0
        logger.info(f"shadow_guardrail_replay_complete: Replayed logs for {rule_id}. Total Evaluations: {rule.total_evaluations}, False Positives: {rule.false_positives}")
        
        return {
            "rule_id": rule_id,
            "total_evaluations": rule.total_evaluations,
            "false_positives": rule.false_positives,
            "fp_rate": self.get_false_positive_rate(rule_id),
            "evaluated_hours": rule.evaluated_hours
        }

    def attempt_promotion(self, rule_id: str) -> Dict[str, Any]:
        """
        Attempts to promote a Candidate rule to ACTIVE.
        Demands:
        1. Evaluated for at least 72 hours.
        2. False Positive rate strictly below 0.1% (fp_rate < 0.001).
        3. No policy conflicts (cannot block essential system keywords or libraries).
        """
        rule = self.rules.get(rule_id)
        if not rule:
            raise ValueError(f"Rule {rule_id} not found.")

        if rule.status != GuardrailStatus.CANDIDATE:
            return {"promoted": False, "status": rule.status.value, "reason": "Rule is not a CANDIDATE."}

        # 1. 72-Hour Check
        if rule.evaluated_hours < 72.0:
            reason = f"Insufficient evaluation time. Hours: {rule.evaluated_hours}/72.0"
            logger.warning(f"shadow_guardrail_promotion_denied: Rule {rule_id} - {reason}")
            return {"promoted": False, "status": rule.status.value, "reason": reason}

        # 2. FP Rate Check (Strictly below 0.1%)
        fp_rate = self.get_false_positive_rate(rule_id)
        if fp_rate >= 0.001:
            reason = f"False positive rate too high: {fp_rate:.4%} >= 0.1%"
            rule.status = GuardrailStatus.REJECTED
            logger.error(f"shadow_guardrail_promotion_rejected: Rule {rule_id} - {reason}. Marked as REJECTED.")
            return {"promoted": False, "status": rule.status.value, "reason": reason}

        # 3. Policy Conflict Checks (Essential system keywords)
        conflicts = []
        forbidden_matches = ["RAEContextLocator", "ExperimentManager", "observe_plan_dispatch"]
        for keyword in forbidden_matches:
            if re.search(rule.pattern, keyword):
                conflicts.append(keyword)

        if conflicts:
            reason = f"Policy conflict: Rule blocks essential system keywords/APIs: {conflicts}"
            rule.status = GuardrailStatus.REJECTED
            logger.error(f"shadow_guardrail_promotion_rejected: Rule {rule_id} - {reason}. Marked as REJECTED.")
            return {"promoted": False, "status": rule.status.value, "reason": reason}

        # Automatic Promotion
        rule.status = GuardrailStatus.ACTIVE
        logger.info(f"shadow_guardrail_promoted: Rule {rule_id} promoted automatically to ACTIVE.")
        
        return {
            "promoted": True,
            "status": rule.status.value,
            "fp_rate": fp_rate,
            "evaluated_hours": rule.evaluated_hours,
            "description": rule.description
        }
