"""Minimal test-only stubs for ClearML package to neutralize imports without installation.

Provides no-op classes for common imports: Task, Logger, Dataset. These are safe placeholders
that allow import statements to succeed without side effects or errors. Actual functionality
requires the real ClearML package.
"""


class Task:
    """
    No-op placeholder for clearml.Task.
    Supports common init patterns but performs no actual tracking or logging.
    """

    def __init__(self, project_name=None, task_name=None, **kwargs):
        self.project_name = project_name or "default_project"
        self.task_name = task_name or "default_task"
        self._init_args = kwargs
        self._is_initialized = True

    @classmethod
    def init(
        cls,
        project_name=None,
        task_name=None,
        task_type=None,
        output_uri=None,
        reuse_last_task_id=False,
        auto_connect=True,
        **kwargs,
    ):
        """
        Class method to create/init a Task instance. Returns a no-op instance.
        """
        instance = cls(project_name=project_name, task_name=task_name, **kwargs)
        if auto_connect:
            instance.connect({})
        return instance

    def connect(self, configuration_object=None):
        """No-op connect method."""
        pass

    def get_task(self, task_id=None):
        """Returns self as the task instance."""
        return self

    def close(self):
        """No-op close method."""
        pass

    def set_model(self, model_path, **kwargs):
        """No-op set_model."""
        pass

    def get_model(self):
        """Returns None for model."""
        return None

    # Additional no-op methods for compatibility
    def log_metric(self, name, value, **kwargs):
        pass

    def upload_model(self, model_path, **kwargs):
        pass


class Logger:
    """
    No-op placeholder for clearml.Logger.
    Supports report_scalar and other common logging methods without side effects.
    """

    @staticmethod
    def current_logger():
        """Returns a no-op Logger instance."""
        return Logger()

    def report_scalar(self, title, series, value, iteration=None, **kwargs):
        """No-op scalar reporting."""
        pass

    def report_plotly_plot(self, title, series, iteration=None, figure=None, **kwargs):
        """No-op plotly plot reporting."""
        pass

    def report_table(self, title, series, iteration=None, table_data=None, **kwargs):
        """No-op table reporting."""
        pass

    def report_histogram(self, title, series, histogram_data, **kwargs):
        """No-op histogram reporting."""
        pass

    # Flush/close no-ops
    def flush(self):
        pass

    def close(self):
        pass


class Dataset:
    """
    No-op placeholder for clearml.Dataset.
    Supports get and create patterns but returns None or empty structures.
    """

    @classmethod
    def get(
        cls, dataset_name, project=None, dataset_id=None, output_folder=None, **kwargs
    ):
        """
        Class method to retrieve a dataset. Returns None (no-op).
        """
        return None

    @classmethod
    def create(
        cls, project_name, dataset_name, output_folder=None, version=None, **kwargs
    ):
        """
        Class method to create a dataset. Returns a no-op instance.
        """
        instance = cls(dataset_name=dataset_name)
        instance.project_name = project_name
        instance.version = version or "0.0"
        return instance

    def __init__(self, dataset_name=None):
        self.dataset_name = dataset_name or "default_dataset"
        self.project_name = "default_project"
        self.version = "0.0"
        self._files = []

    def add_files(self, local_files, wildcard=None, **kwargs):
        """No-op file addition."""
        pass

    def get_local_copy(self, target_folder=None, **kwargs):
        """Returns empty path (no-op)."""
        return ""

    def finalize(self, **kwargs):
        """No-op finalization."""
        pass

    def close(self):
        """No-op close."""
        pass


# Additional top-level no-ops if directly imported
def get_logger():
    return Logger()


def TaskInit(project_name=None, task_name=None, **kwargs):
    return Task.init(project_name=project_name, task_name=task_name, **kwargs)
