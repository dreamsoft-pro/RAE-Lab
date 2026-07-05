import logging

class SafeRolloutManager:
    def manage_transition(self, proposal_id: str, current_stage: str, budget_ok: bool = True):
        if not budget_ok:
            logging.warning(f"Rollout BLOCKED for {proposal_id}: Budget exceeded")
            return current_stage
            
        stages = ["offline", "shadow", "canary", "promoted"]
        idx = stages.index(current_stage)
        next_stage = stages[idx + 1] if idx < len(stages) - 1 else current_stage
        return next_stage
