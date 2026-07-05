from rae_core.models.improvement import InsightPack
from typing import List

class StrategyCompiler:
    def compile_insights(self, experiment_results: List[dict]) -> InsightPack:
        return InsightPack(insights=experiment_results, recommendations=["Apply policy patch G-001"])
