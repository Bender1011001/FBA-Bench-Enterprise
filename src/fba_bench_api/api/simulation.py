"""
Simulation manager module.
Handles running simulations inside experiments.
"""


class SimulationManager:
    def __init__(self):
        self.simulations = {}

    def run_simulation(self, sim_id: str, params: dict):
        """Run a new simulation (stub)."""
        self.simulations[sim_id] = {"status": "running", "params": params}

    def stop_simulation(self, sim_id: str):
        """Stop a simulation (stub)."""
        if sim_id in self.simulations:
            self.simulations[sim_id]["status"] = "stopped"

    def get_status(self, sim_id: str) -> dict:
        """Return simulation status (stub)."""
        return self.simulations.get(sim_id, {"status": "unknown"})
