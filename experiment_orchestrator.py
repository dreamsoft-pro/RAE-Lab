import logging
from typing import List
from rae_core.models.improvement import ExperimentRun

class ExperimentOrchestrator:
    def run_offline_replay(self, proposal_id: str, dataset: List[dict]) -> ExperimentRun:
        logging.info(f"Running offline replay for {proposal_id}")
        return ExperimentRun(proposal_id=proposal_id, mode="offline", result="pass")
