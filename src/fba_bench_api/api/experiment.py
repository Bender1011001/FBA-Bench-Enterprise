"""
Experiment manager module.
Coordinates experiment lifecycle, state, and results.
"""

class ExperimentManager:
    def __init__(self):
        self.experiments = {}

    def start_experiment(self, experiment_id: str, config: dict):
        """Start a new experiment (stub)."""
        self.experiments[experiment_id] = {"status": "running", "config": config}

    def stop_experiment(self, experiment_id: str):
        """Stop an experiment (stub)."""
        if experiment_id in self.experiments:
            self.experiments[experiment_id]["status"] = "stopped"

    def get_status(self, experiment_id: str) -> dict:
        """Return experiment status (stub)."""
        return self.experiments.get(experiment_id, {"status": "unknown"})