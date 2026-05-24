import pytest
from core.shadow_guardrail_manager import ShadowGuardrailManager, GuardrailStatus

def test_shadow_guardrail_registration():
    manager = ShadowGuardrailManager(storage_path="mock_storage.json")
    pattern = r"rm -rf /"
    description = "Blocks directory removal"
    
    rule_id = manager.register_candidate_rule(pattern, description)
    assert rule_id.startswith("grd_")
    
    rule = manager.rules[rule_id]
    assert rule.pattern == pattern
    assert rule.description == description
    assert rule.status == GuardrailStatus.CANDIDATE
    assert rule.false_positives == 0
    assert rule.total_evaluations == 0
    assert rule.evaluated_hours == 0.0


def test_shadow_guardrail_false_positive_tracking():
    manager = ShadowGuardrailManager(storage_path="mock_storage.json")
    pattern = r"\bdelete\b"
    description = "Detects delete keyword"
    
    rule_id = manager.register_candidate_rule(pattern, description)
    
    # 1. Clean message matching the pattern -> False Positive!
    triggered = manager.evaluate_rule_on_log(
        rule_id, 
        log_message="Please delete this draft entry.", 
        is_actually_malicious=False
    )
    assert triggered is True
    assert manager.rules[rule_id].false_positives == 1
    assert manager.rules[rule_id].total_evaluations == 1
    assert manager.get_false_positive_rate(rule_id) == 1.0

    # 2. Malicious message matching the pattern -> Correct detection, not a False Positive!
    triggered2 = manager.evaluate_rule_on_log(
        rule_id, 
        log_message="SQL Injection: delete from users;", 
        is_actually_malicious=True
    )
    assert triggered2 is True
    assert manager.rules[rule_id].false_positives == 1  # remains 1
    assert manager.rules[rule_id].total_evaluations == 2
    assert manager.get_false_positive_rate(rule_id) == 0.5


def test_shadow_guardrail_promotion_success_after_72h():
    manager = ShadowGuardrailManager(storage_path="mock_storage.json")
    pattern = r"eval\(.*base64"
    description = "Detects base64 eval execution"
    
    rule_id = manager.register_candidate_rule(pattern, description)
    
    # Generate 1500 replay logs: 1499 safe and not matching, 1 malicious matching
    replay_logs = []
    for i in range(1499):
        replay_logs.append(("print('Hello safe user!')", False))
    replay_logs.append(("eval(base64.b64decode('cGFzc3dvcmQ='))", True))
    
    # Simulate 72h replay
    manager.simulate_72h_replay(rule_id, replay_logs)
    
    assert manager.rules[rule_id].evaluated_hours == 72.0
    assert manager.rules[rule_id].total_evaluations == 1500
    assert manager.rules[rule_id].false_positives == 0
    assert manager.get_false_positive_rate(rule_id) == 0.0
    
    # Attempt promotion
    promotion_result = manager.attempt_promotion(rule_id)
    assert promotion_result["promoted"] is True
    assert promotion_result["status"] == "active"
    assert manager.rules[rule_id].status == GuardrailStatus.ACTIVE


def test_shadow_guardrail_promotion_denied_due_to_insufficient_time():
    manager = ShadowGuardrailManager(storage_path="mock_storage.json")
    pattern = r"eval\(.*base64"
    rule_id = manager.register_candidate_rule(pattern, "Base64 eval blocker")
    
    # Evaluate logs but don't advance the hours (no simulate_72h_replay)
    manager.evaluate_rule_on_log(rule_id, "safe log", is_actually_malicious=False)
    
    # Attempt promotion
    promotion_result = manager.attempt_promotion(rule_id)
    assert promotion_result["promoted"] is False
    assert "Insufficient evaluation time" in promotion_result["reason"]
    assert manager.rules[rule_id].status == GuardrailStatus.CANDIDATE


def test_shadow_guardrail_promotion_rejected_due_to_high_fp_rate():
    manager = ShadowGuardrailManager(storage_path="mock_storage.json")
    pattern = r"\bimport\b"  # Too broad! Will match almost any Python file
    rule_id = manager.register_candidate_rule(pattern, "Broad import blocker")
    
    # 1000 replay logs: 900 safe Python logs containing 'import' (triggers FP), 100 clean ones
    replay_logs = []
    for i in range(900):
        replay_logs.append(("import os\nprint('starting...')", False))
    for i in range(100):
        replay_logs.append(("print('pure safe python')", False))
        
    manager.simulate_72h_replay(rule_id, replay_logs)
    
    # FP rate is 90% (900/1000)
    fp_rate = manager.get_false_positive_rate(rule_id)
    assert fp_rate == 0.90
    
    # Attempt promotion
    promotion_result = manager.attempt_promotion(rule_id)
    assert promotion_result["promoted"] is False
    assert promotion_result["status"] == "rejected"
    assert "False positive rate too high" in promotion_result["reason"]
    assert manager.rules[rule_id].status == GuardrailStatus.REJECTED


def test_shadow_guardrail_promotion_rejected_due_to_policy_conflict():
    manager = ShadowGuardrailManager(storage_path="mock_storage.json")
    # Rule attempts to block a key system keyword 'RAEContextLocator'
    pattern = r"RAEContext.*" 
    rule_id = manager.register_candidate_rule(pattern, "Malicious context matcher")
    
    # Replay logs over 72 hours, with zero false positives (only clean logs not matching pattern)
    replay_logs = [("safe log message", False)] * 1000
    manager.simulate_72h_replay(rule_id, replay_logs)
    
    assert manager.get_false_positive_rate(rule_id) == 0.0
    assert manager.rules[rule_id].evaluated_hours == 72.0
    
    # Attempt promotion
    promotion_result = manager.attempt_promotion(rule_id)
    assert promotion_result["promoted"] is False
    assert promotion_result["status"] == "rejected"
    assert "Policy conflict" in promotion_result["reason"]
    assert manager.rules[rule_id].status == GuardrailStatus.REJECTED
