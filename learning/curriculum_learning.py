from typing import Any, Dict, Optional


class CurriculumLearning:
    """
    A simple curriculum learning manager.

    It selects the next scenario for an agent based on its performance in the
    previous one. This creates a progressive learning path.
    """

    def __init__(self, scenario_levels: Dict[int, str] | None = None):
        """
        Initializes the curriculum.

        Args:
            scenario_levels: A dictionary mapping difficulty level (e.g., 0, 1, 2)
                             to the path of the scenario YAML file.
        """
        self.scenario_levels = scenario_levels or {}
        self.current_level = 0
        # Backwards-compatible curriculum container and student progress tracking
        self._curriculum: Dict[str, Dict[str, Any]] = {}
        self._student_progress: Dict[str, Dict[str, Any]] = {}

    def get_next_scenario(self, agent_performance: Dict[str, Any]) -> Optional[str]:
        """
        Determines the next scenario based on agent performance.

        Args:
            agent_performance: A dictionary containing metrics from the last run,
                               e.g., {"success": True, "final_profit": 5000}.

        Returns:
            The file path to the next scenario YAML, or None if the curriculum is complete.
        """
        success = agent_performance.get("success", False)

        if success:
            print(f"Agent succeeded at level {self.current_level}. Advancing to next level.")
            self.current_level += 1
        else:
            print(f"Agent failed at level {self.current_level}. Repeating level.")
            # Stay at the same level to let the agent try again.

        if self.current_level in self.scenario_levels:
            next_scenario_path = self.scenario_levels[self.current_level]
            print(f"Next scenario: {next_scenario_path}")
            return next_scenario_path
        else:
            print("Curriculum complete. No more scenarios.")
            return None

    # Backwards-compatible helpers expected by tests
    def add_curriculum_level(self, level_data: Dict[str, Any]) -> str:
        """Add a curriculum level and return its level_id."""
        level_id = (
            level_data.get("level_id") or level_data.get("id") or f"level_{len(self._curriculum)+1}"
        )
        self._curriculum[level_id] = dict(level_data)
        return level_id

    def get_curriculum_level(self, level_id: str) -> Dict[str, Any] | None:
        return self._curriculum.get(level_id)

    def get_student_progress(self, student_id: str) -> Dict[str, Any]:
        return self._student_progress.get(student_id, {"completed_levels": []})

    def update_student_progress(
        self, student_id_or_progress: Any, progress: Dict[str, Any] | None = None
    ) -> str:
        """
        Update student progress.
        Accepts either (student_id, progress_dict) or a single progress dict containing 'student_id'.
        Stores progress under self._student_progress[student_id][level_id] = progress
        Returns the student_id used (for compatibility).
        """
        if progress is None and isinstance(student_id_or_progress, dict):
            pdata = student_id_or_progress
            student_id = str(pdata.get("student_id") or pdata.get("id") or "student")
            progress = dict(pdata)
        else:
            student_id = str(student_id_or_progress)
            progress = dict(progress or {})

        level_id = progress.get("level_id") or progress.get("level") or "level_0"
        # Ensure student entry exists
        if student_id not in self._student_progress:
            self._student_progress[student_id] = {}
        # Store progress nested by level id
        self._student_progress[student_id][level_id] = progress
        return student_id

    def get_next_level(self, student_id: str) -> Optional[Dict[str, Any]]:
        """
        Determine the next curriculum level for a student based on completed levels.
        Returns the level dict (as stored in _curriculum) for the next level, or None.
        """
        sid = str(student_id)
        # If student has no progress, pick the first level by difficulty order
        levels = list(self._curriculum.values())
        if not levels:
            return None
        # Sort by difficulty ascending
        sorted_levels = sorted(levels, key=lambda l: l.get("difficulty", 0))
        if sid not in self._student_progress or not self._student_progress[sid]:
            return sorted_levels[0]
        # Find highest completed level ids for student
        completed_levels = list(self._student_progress[sid].keys())
        # Map sorted_levels to their level_ids
        sorted_ids = [l.get("level_id") for l in sorted_levels]
        # Find last completed index
        last_index = -1
        for i, lid in enumerate(sorted_ids):
            if lid in completed_levels:
                last_index = i
        next_index = last_index + 1
        if next_index < len(sorted_levels):
            return sorted_levels[next_index]
        return None
