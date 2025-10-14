from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GlobalVariables:
    """
    Minimal global variables used by services for headers and metadata.

    At minimum, external_service/mock_service expect `app_version` for the User-Agent header.
    Extend this class conservatively if additional global settings are required elsewhere.
    """
    app_version: str = "0.0.0-dev"


# Singleton-style global variable holder
global_variables = GlobalVariables()