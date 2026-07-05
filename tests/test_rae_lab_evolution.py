import pytest
import sys
import os

# Add src to sys.path so we can import from rae_lab package
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from rae_lab.hypothesis_engine import HypothesisEngine
from rae_lab.failure_mining_engine import FailureMiningEngine
from rae_lab.safe_rollout_manager import SafeRolloutManager
from rae_lab.experiment_orchestrator import ExperimentOrchestrator
from rae_lab.strategy_compiler import StrategyCompiler

# Import models from RAE-core
from rae_core.models.failure import FailureLearningRecord
from rae_core.models.evidence import OutcomeRecord
from rae_contracts import RiskClass, ExecutionStatus

def test_hypothesis_engine_failures():
    engine = HypothesisEngine()
    
    # 2 identical failures should trigger a hypothesis
    failures = [
        FailureLearningRecord(
            failure_id="f1",
            task_id="t1",
            trace_id="tr1",
            failure_type="recursion_error",
            failure_stage="sandbox",
            wasted_cost=0.01,
            lesson_learned="Increase recursion limit",
            future_guardrail="guard_rec",
            retry_recommendation="increase"
        ),
        FailureLearningRecord(
            failure_id="f2",
            task_id="t2",
            trace_id="tr2",
            failure_type="recursion_error",
            failure_stage="sandbox",
            wasted_cost=0.02,
            lesson_learned="Increase recursion limit",
            future_guardrail="guard_rec",
            retry_recommendation="increase"
        )
    ]
    
    hyps = engine.generate_from_failures(failures)
    assert len(hyps) == 1
    assert "recursion_error" in hyps[0].statement


def test_failure_mining():
    engine = FailureMiningEngine()
    
    failures = [
        FailureLearningRecord(
            failure_id="f1",
            task_id="t1",
            trace_id="tr1",
            failure_type="timeout",
            failure_stage="sandbox",
            wasted_cost=10.0,
            lesson_learned="Increase timeout",
            future_guardrail="guard_timeout",
            retry_recommendation="increase"
        ),
        FailureLearningRecord(
            failure_id="f2",
            task_id="t2",
            trace_id="tr2",
            failure_type="timeout",
            failure_stage="sandbox",
            wasted_cost=15.0,
            lesson_learned="Increase timeout",
            future_guardrail="guard_timeout",
            retry_recommendation="increase"
        )
    ]
    
    pack = engine.mine(failures)
    # The mine method returns a FailurePatternPack or dict
    if hasattr(pack, "patterns"):
        assert len(pack.patterns) == 1
        assert pack.patterns[0]["pattern"] == "timeout"
        assert pack.patterns[0]["avg_cost"] == 12.5
    else:
        assert len(pack["patterns"]) == 1
        assert pack["patterns"][0]["pattern"] == "timeout"


def test_safe_rollout_manager():
    manager = SafeRolloutManager()
    
    # Next stage from offline is shadow
    next_stage = manager.manage_transition("proposal-1", "offline", budget_ok=True)
    assert next_stage == "shadow"
    
    # Budget exceeded blocks transition
    next_stage = manager.manage_transition("proposal-1", "offline", budget_ok=False)
    assert next_stage == "offline"


def test_experiment_orchestrator():
    orch = ExperimentOrchestrator()
    run = orch.run_offline_replay("proposal-1", [])
    assert run.proposal_id == "proposal-1"
    assert run.mode == "offline"
    assert run.result == "pass"


def test_strategy_compiler():
    compiler = StrategyCompiler()
    pack = compiler.compile_insights([{"accuracy": 0.95}])
    assert len(pack.insights) == 1
    assert "G-001" in pack.recommendations[0]
